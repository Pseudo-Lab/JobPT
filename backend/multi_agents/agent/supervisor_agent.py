from typing import cast
from langgraph.prebuilt import create_react_agent
from langchain_upstage import ChatUpstage
from langchain_core.messages import AIMessage, SystemMessage
from multi_agents.states.states import State
from multi_agents.prompts.supervisor_prompt import get_supervisor_prompt
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler

import json
import re
from configs import AGENT_MODEL, UPSTAGE_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY


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
    agent_outputs = state.get("agent_outputs", {})
    collected_info = ""
    if agent_outputs:
        if "summary" in agent_outputs:
            collected_info += f"\n[회사 정보 요약]\n{agent_outputs['summary']}\n"
        if "suggestion" in agent_outputs:
            collected_info += f"\n[이력서 개선 제안]\n{agent_outputs['suggestion']}\n"

    # 이미 호출된 agent 목록 확인
    called_agents = list(agent_outputs.keys()) if agent_outputs else []

    # 사용자 입력 추출 (첫 번째 HumanMessage)
    user_input = ""
    messages_list = state.get("messages", [])
    
    for msg in messages_list:
        if hasattr(msg, 'content') and msg.__class__.__name__ == 'HumanMessage':
            print("msg: ", msg.content)
            user_input = msg.content
            break
    
    # 프롬프트 생성 (외부 파일에서 가져오기)
    formatted_message = get_supervisor_prompt(
        user_input=user_input,
        user_resume=state.get("user_resume", ""),
        company_name=state.get("company_name", ""),
        job_description=state.get("job_description", ""),
        called_agents=called_agents,
        collected_info=collected_info,
    )

    langfuse_handler = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host="https://cloud.langfuse.com"  # Optional: defaults to https://cloud.langfuse.com
    )

    # Initialize the Langfuse handler
    langfuse_handler = CallbackHandler()

    messages = [SystemMessage(content=formatted_message), *messages_list]

    # ReAct agent 생성 (도구 없이 의사결정만)
    agent = create_react_agent(model, [])
    response = cast(AIMessage, await agent.ainvoke({"messages": messages}, config={"callbacks": [langfuse_handler]}))

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
    final_answer = state.get("final_answer", "")
    if final_answer:
        return {"messages": [AIMessage(content=final_answer)]}

    # fallback: 마지막 메시지 반환
    messages_list = state.get("messages", [])
    if messages_list:
        return {"messages": [messages_list[-1]]}
    return {"messages": []}
