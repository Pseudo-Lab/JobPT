import os
import asyncio

from openai import OpenAI
from typing_extensions import Annotated
from dataclasses import dataclass, field
from typing import Dict, List, cast, Annotated, Sequence
from dotenv import load_dotenv

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, AnyMessage
from langgraph.graph import StateGraph, add_messages
from langchain_mcp_adapters.client import MultiServerMCPClient
from states.states import State

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4.1-mini"


async def suggest_agent(state: State):
    """
    이력서와 요약 정보를 바탕으로 개선 제안 생성
    """
    # OpenAI API 사용
    system_message = f"""
You are an expert in resume improvement.

Refer to the resume and the job (company) summary provided below, and generate 3 to 5 specific and practical improvement suggestions based on the following guidelines:

[Guidelines]
- Each suggestion must be written clearly in a single sentence.
- Incorporate both the resume and the job summary into your suggestions.
- Provide recommendations from various perspectives, such as relevant experience, skills, achievements, projects, leadership, and alignment with the latest industry trends.
- Offer concrete and actionable ideas that would meaningfully enhance or add to the resume.

[Resume]
{state.user_resume}

[Job Summary]
{state.company_summary}
"""
    print(state)
    model = ChatOpenAI(model=MODEL, temperature=0, api_key=OPENAI_API_KEY)

    async with MultiServerMCPClient() as client:
        agent = create_react_agent(model, client.get_tools())

        messages = [SystemMessage(content=system_message), *state.messages]

        response = cast(AIMessage, await agent.ainvoke({"messages": messages}))

    return {"messages": [response["messages"][-1]], "agent_name": "suggestion_agent"}
