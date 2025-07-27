import asyncio
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import AIMessage, SystemMessage
from multi_agents.states.states import State
from typing import Dict, List, cast
from configs import *


async def summary_agent(state: State) -> Dict[str, List[AIMessage]]:

    model = ChatOpenAI(model=AGENT_MODEL, temperature=0, api_key=OPENAI_API_KEY)

    # Option 1 from error message: client = MultiServerMCPClient(...)
    client = MultiServerMCPClient(
        {"tavily-mcp": {"command": "npx", "args": ["-y", "@smithery/cli@latest", "run", "@tavily-ai/tavily-mcp", "--key", os.getenv("SMITHERY_API_KEY")], "transport": "stdio"}}
    )
    tools = await client.get_tools()
    agent = create_react_agent(model, tools)

    system_message = f"""You are an assistant specialized in gathering and summarizing company-related information. 
    Given a company name as input, your task is to search the web and relevant platforms (including news articles, company websites, blogs, and YouTube) to collect and summarize key insights about the company.

    Company Name: {state.company_name}

    Focus on the following aspects:
    Industry & Domain
    - Describe the industry and market the company operates in.
    - Include recent trends in the domain based on news articles.

    Competitive Edge
    - Highlight the company's differentiators and strengths compared to major competitors in the same industry.
    - Support with insights from news articles.

    Key Services
    - Summarize the core services or products relevant to the job description.
    - Focus on offerings mentioned in news articles or recent updates.

    Talent Fit
    - Identify the type of candidates the company looks for, based on its official website's careers or recruitment pages.

    Team Culture
    - Describe the corporate or team culture, referencing company blogs, interviews, or YouTube videos.

    Ongoing Projects & Initiatives
    - List notable ongoing projects, research areas, or innovation initiatives related to the job role, found in news articles or official announcements.

    Use available tools such as web search and YouTube search to find the most relevant and up-to-date information.
    """

    messages = [SystemMessage(content=system_message), *state.messages]
    response = cast(AIMessage, await agent.ainvoke({"messages": messages}))
    return {"messages": [response["messages"][-1]], "agent_name": "summary_agent", "company_summary": response["messages"][-1].content}
