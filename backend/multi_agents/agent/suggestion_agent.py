from typing import cast

from langgraph.prebuilt import create_react_agent
from langchain_upstage import ChatUpstage
from langchain_core.messages import AIMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from multi_agents.states.states import State
from langchain_core.tools import tool
from configs import AGENT_MODEL, UPSTAGE_API_KEY  # 필요한 설정만 import


@tool
def search(url: str) -> str:
    """
    블로그 URL을 기반으로 웹에서 검색해주는 도구

    Args:
        url (str): 검색할 블로그 URL

    Returns:
        str: 검색 결과 (현재는 더미 데이터)
    """
    # TODO: 실제 웹 검색 로직 구현 필요
    return "search tool"


async def suggest_agent(state: State):
    """
    이력서와 요약 정보를 바탕으로 개선 제안을 생성하는 에이전트

    Args:
        state (State): 현재 상태 정보 (이력서, 직무 설명, 회사 정보 등 포함)

    Returns:
        dict: 응답 메시지와 에이전트 이름을 포함한 딕셔너리
    """
    # 시스템 메시지 구성 - 이력서 개선 전문가 역할 정의
    system_message = f"""
당신은 이력서 개선 전문가입니다.

당신의 임무는 **선택된 이력서(Selected Resume)** 섹션을 수정하여, 지원하는 직무와 회사에 맞게 명확성, 임팩트, 관련성을 강화하는 것입니다. 단, 원래의 이력서 형식과 톤은 유지해야 합니다.

[지침]
- 원래의 구조와 전문적인 이력서 스타일(예: 불릿 포인트, 톤)을 유지하세요.  
- 불필요하게 전부 다시 쓰지 말고, 효과를 높이는 데 필요한 부분만 수정하세요.  
- 명확성, 강력한 행동 동사 사용, 수치화된 성과, 직무 설명 및 회사 가치와의 관련성에 집중하세요.  
- 새로운 경험을 만들어내거나 가정하지 말고, 제공된 내용만 기반으로 개선하세요.  
- 두 부분을 반환하세요:  
  1. 개선된 "Selected Resume" 섹션 (이력서에 바로 사용할 수 있는 형식)  
  2. 무엇을 왜 개선했는지에 대한 1–2문장 설명 (간결하고 구체적으로)  

- 원본 이력서의 언어를 그대로 사용하세요. 예를 들어, 원본 이력서가 영어라면, 수정된 내용도 반드시 한국어로 작성해야 합니다.

- 이력서나 사용자 메시지에서 블로그 주소(URL)를 발견하면, 반드시 그 블로그 주소를 입력값으로 검색 도구를 호출하세요.  
- 변경된 부분은 **굵게 표시**하세요.  

[Job Description]  
{state.job_description}  

[Company Summary]  
{state.company_summary}  

[Full Resume]  
{state.resume}  

[Selected Resume Section to Improve]  
{state.user_resume}  
"""
    # Upstage API 사용 (solar-pro2)
    model = ChatUpstage(
        model=AGENT_MODEL, 
        temperature=0,
        api_key=UPSTAGE_API_KEY
    )

    client = MultiServerMCPClient()
    tools = await client.get_tools()

    # React 에이전트 생성
    agent = create_react_agent(model, tools)

    # 메시지 구성 (시스템 메시지 + 기존 대화 내역)
    messages = [SystemMessage(content=system_message), *state.messages]

    response = cast(AIMessage, await agent.ainvoke({"messages": messages}))
    return {"messages": [response["messages"][-1]], "agent_name": "suggestion_agent"}
