from typing import cast

from langgraph.prebuilt import create_react_agent
from langchain_upstage import ChatUpstage
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from multi_agents.states.states import State
from multi_agents.prompts.suggestion_prompt import get_suggestion_prompt
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from multi_agents.tools.github_tools import GITHUB_TOOLS
from multi_agents.tools.blog_tools import BLOG_TOOLS
from configs import AGENT_MODEL, UPSTAGE_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, OPENAI_API_KEY 

async def suggest_agent(state: State):
    """
    이력서와 요약 정보를 바탕으로 개선 제안을 생성하는 에이전트

    Args:
        state (State): 현재 상태 정보 (이력서, 직무 설명, 회사 정보 등 포함)

    Returns:
        dict: 응답 메시지와 에이전트 이름을 포함한 딕셔너리
    """
    # 프롬프트 생성 (외부 파일에서 가져오기)
    agent_outputs = state.get("agent_outputs", {})
    
    system_message = get_suggestion_prompt(
        job_description=state.get("job_description", ""),
        company_summary=agent_outputs.get("summary", ""),
        resume=state.get("resume", "")
    )

    langfuse_handler = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host="https://cloud.langfuse.com",  # Optional: defaults to https://cloud.langfuse.com
    )

    # Initialize the Langfuse handler
    langfuse_handler = CallbackHandler()

    model = ChatUpstage(model=AGENT_MODEL, temperature=0, api_key=UPSTAGE_API_KEY)
    # model = ChatOpenAI(model=AGENT_MODEL, temperature=0, api_key=OPENAI_API_KEY)

    # GitHub API 도구 및 블로그 도구 사용
    all_tools = GITHUB_TOOLS + BLOG_TOOLS
    print(f"✓ 총 도구 수: {len(all_tools)}개 (GitHub: {len(GITHUB_TOOLS)}, Blog: {len(BLOG_TOOLS)})")

    # React 에이전트 생성 (GitHub API 도구 + 블로그 도구)
    agent = create_react_agent(model, all_tools)

    config = {"recursion_limit": 20, "max_iterations": 10, "callbacks": [langfuse_handler]}
    # 메시지 구성 (시스템 메시지 + 기존 대화 내역)
    messages_list = state.get("messages", [])
    messages = [SystemMessage(content=system_message), *messages_list]

    response = cast(AIMessage, await agent.ainvoke({"messages": messages}, config=config))

    result_content = response["messages"][-1].content
    print("=============suggestion_agent=============")
    print(result_content[:500] + "..." if len(result_content) > 500 else result_content)

    # agent_outputs에 결과 저장 (기존 결과 유지하면서 추가)
    agent_outputs = state.get("agent_outputs", {})
    updated_outputs = {**agent_outputs, "suggestion": result_content}

    return {
        "messages": [response["messages"][-1]],
        "agent_name": "suggestion_agent",
        "agent_outputs": updated_outputs,
    }
