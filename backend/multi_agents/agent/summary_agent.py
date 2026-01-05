import asyncio
from langgraph.prebuilt import create_react_agent
from langchain_upstage import ChatUpstage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import AIMessage, SystemMessage
from multi_agents.states.states import State
from multi_agents.prompts.summary_prompt import get_summary_prompt
from typing import Dict, List, cast
from configs import *


async def summary_agent(state: State) -> Dict[str, List[AIMessage]]:

    model = ChatUpstage(model=AGENT_MODEL, temperature=0, api_key=UPSTAGE_API_KEY)

    # Option 1 from error message: client = MultiServerMCPClient(...)
    try:
        client = MultiServerMCPClient(
            {
                "tavily-mcp": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@smithery/cli@latest",
                        "run",
                        "@tavily-ai/tavily-mcp",
                        "--key",
                        os.getenv("SMITHERY_API_KEY"),
                    ],
                    "transport": "stdio",
                }
            }
        )
        tools = await client.get_tools()
        agent = create_react_agent(model, tools)
    except Exception as e:
        print("summary_agent mcp error:", e)
        agent = create_react_agent(model, [])

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
