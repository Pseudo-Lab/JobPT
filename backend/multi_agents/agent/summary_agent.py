import asyncio
import os
from langgraph.prebuilt import create_react_agent
from langchain_upstage import ChatUpstage
from langchain_core.messages import AIMessage, SystemMessage
from multi_agents.states.states import State
from multi_agents.prompts.summary_prompt import get_summary_prompt
from typing import Dict, List, cast
from configs import *

# Tavily 도구 import
try:
    from langchain_community.tools.tavily_search import TavilySearchResults
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("Warning: langchain_community not available. Tavily search will be disabled.")


async def summary_agent(state: State) -> Dict[str, List[AIMessage]]:

    model = ChatUpstage(model=AGENT_MODEL, temperature=0, api_key=UPSTAGE_API_KEY)

    # Tavily 검색 도구 설정
    tools = []
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if TAVILY_AVAILABLE and tavily_api_key:
            tavily_tool = TavilySearchResults(
                max_results=5,
                api_key=tavily_api_key
            )
            tools = [tavily_tool]
            print("Tavily search tool enabled")
        else:
            print("Tavily search tool disabled: API key not found or package not installed")
    except Exception as e:
        print(f"Error initializing Tavily tool: {e}")
    
    agent = create_react_agent(model, tools)

    # 프롬프트 생성 (외부 파일에서 가져오기)
    system_message = get_summary_prompt(company_name=state.get("company_name", ""))

    messages_list = state.get("messages", [])
    messages = [SystemMessage(content=system_message), *messages_list]
    response = cast(AIMessage, await agent.ainvoke({"messages": messages}))

    result_content = response["messages"][-1].content
    print("=============summary_agent=============")
    print(result_content[:500] + "..." if len(result_content) > 500 else result_content)

    # agent_outputs에 결과 저장 (기존 결과 유지하면서 추가)
    agent_outputs = state.get("agent_outputs", {})
    updated_outputs = {**agent_outputs, "summary": result_content}

    return {
        "messages": [response["messages"][-1]],
        "agent_name": "summary_agent",
        "agent_outputs": updated_outputs,
    }
