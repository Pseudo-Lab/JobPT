from typing import cast
from openai import OpenAI
from langgraph.prebuilt import create_react_agent
from langchain_upstage import ChatUpstage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import AIMessage, SystemMessage
from multi_agents.states.states import State
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

import json
import re
from configs import *  # 필요한 모든 설정 import

client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1"
)


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


async def router(state: State):
    """
    사용자 입력을 분석하여 적절한 에이전트 실행 순서를 결정하는 라우터 함수

    Args:
        state (State): 현재 상태 정보 (사용자 입력, 이력서 등 포함)

    Returns:
        dict: 라우팅 결정이 포함된 메시지 딕셔너리
    """
    model = ChatUpstage(model=AGENT_MODEL, temperature=0, api_key=UPSTAGE_API_KEY)

    # client = MultiServerMCPClient()
    # tools = await client.get_tools()
    tools = []
    agent = create_react_agent(model, tools)

    # 라우팅을 위한 시스템 메시지 구성
    # 사용자 입력과 이력서 정보를 바탕으로 적절한 에이전트 실행 순서 결정
    system_message = """
user_input: {user_input}
user_resume: {user_resume}
---
이 시스템은 이력서를 개선하기 위해 Summary Agent와 Suggestion Agent를 사용합니다.

Summary Agent: 사용자가 제공한 채용공고와 관련된 회사 정보를 찾아 요약합니다.  
Suggestion Agent: 사용자가 지정한 이력서 부분과 요약된 회사 정보를 기반으로 구체적인 개선 제안을 생성합니다.  

아래의 실행 시퀀스 중 하나를 선택하여 한 줄로 출력하세요 (옵션 중 정확히 하나만 선택):  

1. END: 입력이 단순 질문으로 Summary 또는 Suggestion Agent가 필요하지 않거나, user_resume이 비어 있을 때  
2. summary: Summary Agent만 필요한 경우  
3. summary_suggestion: 이력서를 개선하기 위해 Summary Agent와 Suggestion Agent 모두 필요한 경우  
4. suggestion: 회사 요약 정보 없이 Suggestion Agent만 필요한 경우  

각 요청마다 JSON 형식으로 결과를 출력하세요.  
출력 시 'sequence' 키만 포함하고, 그 외 키는 절대 포함하지 마세요.  

출력 예시:  
{{
    sequence: "END"
}}  
{{
    sequence: "summary"
}}  
{{
    sequence: "summary_suggestion"
}}  
{{
    sequence: "suggestion"
}}  
"""
    # 시스템 메시지에 현재 상태 정보 삽입
    system_message = system_message.format(user_input=state.messages, user_resume=state.user_resume)

    messages = [SystemMessage(content=system_message), *state.messages]

    response = cast(AIMessage, await agent.ainvoke({"messages": messages}))

    result = response["messages"][-1].content
    print("=============router=============")
    print(result)
    try:
        data = parse_json_loose(result)
        seq = data.get("sequence", "END")
    except Exception as e:
        print("router json parse error:", e)
        seq = "END"
    state.route_decision = seq
    response["messages"][-1].content = seq
    return {"messages": [response["messages"][-1]]}


def refine_answer(state: State) -> dict:
    """
    최종 사용자 응답을 다듬고 개선하는 함수

    Args:
        state (State): 현재 상태 정보

    Returns:
        dict: 개선된 응답 메시지를 포함한 딕셔너리
    """
    # ChatUpstage 모델 초기화
    model = ChatUpstage(model=AGENT_MODEL, temperature=0, api_key=UPSTAGE_API_KEY)

    # 응답 개선을 위한 시스템 메시지
    # 원본 의미와 구조를 유지하면서 명확성과 문법을 개선
    system_message = """
당신은 사용자에게 제공될 최종 답변을 다듬는 어시스턴트입니다.

아래는 원래 사용자 입력과 어시스턴트의 초안 답변입니다:
- User Input: {user_input}
- Assistant Draft Response: {assistant_response}

만약 Assistant Draft Response가 'END'라면, 사용자 입력에 집중하여 즉흥적으로 답변을 생성하세요.
절대 'END'라고 그대로 반환하지 마세요.

당신의 임무는 초안을 **가볍게 다듬는 것**이며, 의미, 톤, 구조는 변경하지 마세요.  
핵심 세부 사항은 모두 유지해야 합니다.  
명확성, 문법, 흐름 개선이 필요한 경우에만 손보세요.  

중요한 정보를 삭제하거나 의도를 바꿀 수 있는 식으로 다시 표현하지 마세요.  

**중요**: 마크다운 형식(줄바꿈, 리스트, 굵게 표시 등)을 반드시 유지하세요.  
줄바꿈은 `\n`으로, 리스트는 `-` 또는 `*`로, 굵게 표시는 `**텍스트**`로 작성하세요.  
마크다운 문법이 포함되어 있다면 그대로 유지하세요.

어시스턴트의 답변이 이미 명확하고 적절하다면 그대로 반환하세요.
"""
    prompt = PromptTemplate.from_template(system_message)
    chain = prompt | model | StrOutputParser()

    # 응답 개선 실행
    answer = chain.invoke({"user_input": state.messages[0].content, "assistant_response": state.messages[-1].content})

    print("=============refined_answer=============")
    print(answer)

    return {"messages": [AIMessage(content=answer)]}
