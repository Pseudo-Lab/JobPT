from typing import cast

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from multi_agents.states.states import State
from langchain_core.tools import tool
from configs import AGENT_MODEL  # 필요한 설정만 import


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
You are a resume improvement expert.

Your task is to revise the **Selected Resume** section to improve clarity, impact, and relevance to the job and company—while preserving the original resume format and tone.

[Instructions]
- Keep the original structure and professional resume style (e.g., bullet points, tone).
- Only revise what’s necessary to enhance effectiveness—do not rewrite everything.
- Focus on clarity, stronger action verbs, quantifiable results, and relevance to the job description and company values.
- Do not invent or assume new experiences—only improve based on what's provided.
- Return two parts:
  1. The improved "Selected Resume" section (in resume-ready format).
  2. A 1-2 sentence explanation of what was improved and why (be concise and specific).

- Use the same language as the original resume. For example, if the resume is written in English, your revisions must also be in English—even if the user query or instructions are in another language.

- If you find a blog address (URL) in the resume or user message, always call the search tool with that blog address as input.
- Please highlight the changes in bold.

[Job Description]
{state.job_description}

[Company Summary]
{state.company_summary}

[Full Resume]
{state.resume}

[Selected Resume Section to Improve]
{state.user_resume}
"""
    model = ChatOpenAI(model=AGENT_MODEL, temperature=0)

    # MCP 클라이언트를 통해 도구들을 가져오고 에이전트 실행
    async with MultiServerMCPClient() as client:
        # 사용 가능한 도구들 수집 (MCP 도구 + 커스텀 검색 도구)
        tools = client.get_tools() + [search]

        # React 에이전트 생성
        agent = create_react_agent(model, tools)

        # 메시지 구성 (시스템 메시지 + 기존 대화 내역)
        messages = [SystemMessage(content=system_message), *state.messages]

        response = cast(AIMessage, await agent.ainvoke({"messages": messages}))
    return {"messages": [response["messages"][-1]], "agent_name": "suggestion_agent"}
