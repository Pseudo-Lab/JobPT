import os
import asyncio
import logging
from dataclasses import dataclass, field
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, AnyMessage
from langgraph.graph import StateGraph, add_messages
from typing_extensions import Annotated
from typing import Dict, List, cast, Annotated, Sequence
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# API 키 확인
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY가 환경 변수에 설정되어 있지 않습니다.")

@dataclass
class State:
    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
            default_factory=list
    )

async def call_model(
    state: State
) -> Dict[str, List[AIMessage]]:
    
    model = ChatOpenAI(
        model="gpt-4o-mini",  
        temperature=0,
        api_key=OPENAI_API_KEY
    )

    async with MultiServerMCPClient({
        # "youtube-data-mcp-server": {
        #     "command": "npx",
        #     "args": [
        #     "-y", 
        #     "@smithery/cli@latest",
        #     "run",
        #     "@icraft2170/youtube-data-mcp-server",
        #     "--key",
        #     "f9a4f6dd-ddff-4eeb-8e40-49a298c7e817"
        #     ]
        # },
        "tavily-mcp": {
            "command": "npx",
            "args": [
            "-y",
            "@smithery/cli@latest",
            "run",
            "@tavily-ai/tavily-mcp",
            "--key",
            "f9a4f6dd-ddff-4eeb-8e40-49a298c7e817"
            ]
        }
    }) as client:
        agent = create_react_agent(model, client.get_tools())
        
        system_message = """You are an assistant specialized in gathering and summarizing company-related information. 
        Given a company name as input, your task is to search the web and relevant platforms (including news articles, company websites, blogs, and YouTube) to collect and summarize key insights about the company.

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

        messages = [
            SystemMessage(content=system_message),
            *state.messages
        ]
        
        response = cast(AIMessage, await agent.ainvoke({"messages": messages}))
        
        return {"messages": [response["messages"][-1]]}
    
async def main(query: str):
    
    builder = StateGraph(State)
    builder.add_node("call_model", call_model)

    builder.add_edge("__start__", "call_model")
    builder.add_edge("call_model", "__end__")

    graph = builder.compile()
    
    result = await graph.ainvoke({"messages": [HumanMessage(content=query)]})
    return result


if __name__ == "__main__":
    query = "The company name is Intel"

    summary_result = asyncio.run(main(query))
    print(summary_result)