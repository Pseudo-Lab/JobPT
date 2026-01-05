from typing import cast
from langgraph.prebuilt import create_react_agent
from langchain_upstage import ChatUpstage
from langchain_core.messages import AIMessage, SystemMessage
from multi_agents.states.states import State

import json
import re
from configs import AGENT_MODEL, UPSTAGE_API_KEY


def parse_json_loose(text: str) -> dict:
    # 코드펜스 제거
    cleaned = re.sub(r"```[a-zA-Z]*\n?|```", "", text).strip()
    # 첫 번째 {...} 블록만 추출
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if not m:
        raise ValueError("No JSON object found in LLM output")
    obj = m.group(0)
    # 따옴표 없는 키에 따옴표 부여: {sequence: "x"} -> {"sequence": "x"}
    obj = re.sub(r"(\{|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1 "\2":', obj)
    return json.loads(obj)


async def supervisor(state: State):
    """
    Supervisor Loop 패턴의 핵심 함수
    - 현재 상태를 분석하여 다음 agent를 선택하거나 FINISH
    - FINISH 시 최종 답변 생성
    """
    model = ChatUpstage(model=AGENT_MODEL, temperature=0, api_key=UPSTAGE_API_KEY)

    # 이미 수집된 agent 결과 포맷팅
    collected_info = ""
    if state.agent_outputs:
        if "summary" in state.agent_outputs:
            collected_info += f"\n[회사 정보 요약]\n{state.agent_outputs['summary']}\n"
        if "suggestion" in state.agent_outputs:
            collected_info += f"\n[이력서 개선 제안]\n{state.agent_outputs['suggestion']}\n"

    # 이미 호출된 agent 목록 확인
    called_agents = list(state.agent_outputs.keys()) if state.agent_outputs else []

    system_message = """당신은 이력서 개선 시스템의 Supervisor입니다.
사용자의 요청과 현재 상태를 분석하여 다음 행동을 결정합니다.

[현재 상태]
- 사용자 입력: {user_input}
- 선택된 이력서 부분: {user_resume}
- 회사명: {company_name}
- 채용공고: {job_description}
- 이미 호출된 Agent: {called_agents}
- 이미 수집된 정보: {collected_info}

[사용 가능한 Agent]
1. summary - 회사 정보를 검색하고 요약합니다. 회사에 대한 정보가 필요할 때 사용합니다.
2. suggestion - 이력서 개선 제안을 생성합니다. 이력서를 수정/개선해야 할 때 사용합니다.

[의사결정 규칙 - 반드시 준수]
1. **이미 호출된 Agent는 절대 다시 호출하지 마세요!**
   - "이미 호출된 Agent" 목록에 있는 agent는 선택할 수 없습니다.
   - 결과가 불완전하더라도 같은 agent를 재호출하지 마세요.
2. 단순한 인사나 일반 질문은 바로 FINISH를 선택하세요.
3. 필요한 agent가 모두 호출되었거나, 호출할 agent가 없으면 FINISH를 선택하세요.
4. FINISH 시 수집된 정보를 바탕으로 최종 답변을 생성하세요.

[출력 형식 - 반드시 JSON으로 출력]
{{
    "next_agent": "summary" | "suggestion" | "FINISH",
    "reasoning": "이 선택을 한 이유",
    "final_answer": "FINISH인 경우에만 최종 답변 작성. 다른 경우 빈 문자열"
}}

중요:
- FINISH를 선택하면 final_answer에 사용자에게 전달할 최종 답변을 반드시 작성하세요.
- 최종 답변은 수집된 정보를 바탕으로 친절하고 도움이 되게 작성하세요.
- 마크다운 형식을 사용하세요.
"""

    # 사용자 입력 추출 (첫 번째 HumanMessage)
    user_input = ""
    for msg in state.messages:
        if hasattr(msg, 'content') and msg.__class__.__name__ == 'HumanMessage':
            user_input = msg.content
            break

    formatted_message = system_message.format(
        user_input=user_input,
        user_resume=state.user_resume or "(없음)",
        company_name=state.company_name or "(없음)",
        job_description=state.job_description[:500] + "..." if len(state.job_description) > 500 else state.job_description or "(없음)",
        called_agents=called_agents if called_agents else "(없음)",
        collected_info=collected_info or "(없음)"
    )

    messages = [SystemMessage(content=formatted_message), *state.messages]

    # ReAct agent 생성 (도구 없이 의사결정만)
    agent = create_react_agent(model, [])
    response = cast(AIMessage, await agent.ainvoke({"messages": messages}))

    result = response["messages"][-1].content
    print("=============supervisor=============")
    print(result)

    # 기본값 초기화
    next_agent = "FINISH"
    reasoning = ""
    final_answer = ""

    try:
        data = parse_json_loose(result)
        next_agent = data.get("next_agent", "FINISH")
        reasoning = data.get("reasoning", "")
        final_answer = data.get("final_answer", "")
    except Exception as e:
        print("supervisor json parse error:", e)
        # 파싱 실패 시 원본 응답을 최종 답변으로 사용
        final_answer = result

    # next_agent 유효성 검사
    if next_agent not in {"summary", "suggestion", "FINISH"}:
        next_agent = "FINISH"

    print(f"next_agent: {next_agent}")
    print(f"reasoning: {reasoning}")

    # 상태 업데이트
    update = {
        "next_agent": next_agent,
    }

    if next_agent == "FINISH":
        update["final_answer"] = final_answer
        update["messages"] = [AIMessage(content=final_answer)]

    return update


# 하위 호환성을 위해 기존 함수명 유지 (deprecated)
async def router(state: State):
    """
    [Deprecated] supervisor() 함수를 사용하세요.
    하위 호환성을 위해 유지됩니다.
    """
    return await supervisor(state)


def refine_answer(state: State) -> dict:
    """
    [Deprecated] supervisor가 최종 답변을 직접 생성하므로 더 이상 사용하지 않습니다.
    하위 호환성을 위해 유지됩니다.
    """
    # 이미 final_answer가 있으면 그대로 반환
    if state.final_answer:
        return {"messages": [AIMessage(content=state.final_answer)]}

    # fallback: 마지막 메시지 반환
    return {"messages": [state.messages[-1]]}
