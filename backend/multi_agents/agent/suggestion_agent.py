from typing import cast

from langgraph.prebuilt import create_react_agent
from langchain_upstage import ChatUpstage
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from multi_agents.states.states import State
from langchain_core.tools import tool
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from multi_agents.agent.github_tools import GITHUB_TOOLS
from multi_agents.agent.blog_tools import BLOG_TOOLS
from configs import AGENT_MODEL, UPSTAGE_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY


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

- 이력서나 사용자 메시지에서 GitHub URL(예: https://github.com/username 또는 https://github.com/owner/repo)을 발견하면, 
  반드시 GitHub API 도구를 사용하여 해당 사용자나 레포지토리의 정보를 조회하세요.
  - 사용자/조직 정보: get_github_user_info, list_github_user_repos
  - 레포지토리 상세: get_github_repo_details, get_github_repo_readme
  - 개발 활동: get_github_repo_commits, get_github_repo_languages, get_github_repo_contributors

- 이력서나 사용자 메시지에서 블로그 URL(예: Medium, Tistory, Naver, Velog, custom sites)을 발견하면,
  반드시 Blog 도구를 사용하여 블로그의 내용과 활동을 분석하세요.
  - 블로그 개요: fetch_homepage_overview (제목, 설명, 카테고리)
  - 최근 게시물: list_recent_posts (제목, 날짜, 요약)
  - 게시물 상세: fetch_post_content (본문 내용, 태그)
  - 작성자 분석: analyze_blog_author (주제, 작성 스타일)
  
- 변경된 부분은 **굵게 표시**하세요.  

[Job Description]  
{state.job_description}  

[Company Summary]  
{state.agent_outputs.summary}

[Full Resume]  
{state.resume}  

"""

    langfuse_handler = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host="https://cloud.langfuse.com",  # Optional: defaults to https://cloud.langfuse.com
    )

    # Initialize the Langfuse handler
    langfuse_handler = CallbackHandler()

    model = ChatUpstage(model=AGENT_MODEL, temperature=0, api_key=UPSTAGE_API_KEY)
    # model = ChatOpenAI(model=AGENT_MODEL, temperature=0, api_key=OPENAI_API_KEY)

    # MCP 도구와 GitHub 도구 결합
    try:
        client = MultiServerMCPClient()
        mcp_tools = await client.get_tools()
        print(f"✓ MCP Tools 로드: {len(mcp_tools)}개")
    except Exception as e:
        print(f"⚠️ MCP Tools 로드 실패: {e}")
        mcp_tools = []

    # GitHub API 도구들 추가
    all_tools = mcp_tools + GITHUB_TOOLS + BLOG_TOOLS
    print(f"✓ 총 도구 수: {len(all_tools)}개 (MCP: {len(mcp_tools)}, GitHub: {len(GITHUB_TOOLS)})")

    # React 에이전트 생성 (MCP 도구 + GitHub API 도구)
    agent = create_react_agent(model, all_tools)

    config = {"recursion_limit": 20, "max_iterations": 10, "callbacks": [langfuse_handler]}
    # 메시지 구성 (시스템 메시지 + 기존 대화 내역)
    messages = [SystemMessage(content=system_message), *state.messages]

    response = cast(AIMessage, await agent.ainvoke({"messages": messages}, config=config))

    result_content = response["messages"][-1].content
    print("=============suggestion_agent=============")
    print(result_content[:500] + "..." if len(result_content) > 500 else result_content)

    # agent_outputs에 결과 저장 (기존 결과 유지하면서 추가)
    updated_outputs = {**state.agent_outputs, "suggestion": result_content}

    return {
        "messages": [response["messages"][-1]],
        "agent_name": "suggestion_agent",
        "agent_outputs": updated_outputs,
    }
