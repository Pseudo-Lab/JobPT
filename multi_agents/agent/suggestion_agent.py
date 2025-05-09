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
  2. A 1–2 sentence explanation of what was improved and why (be concise and specific).

- Use the same language as the original resume. For example, if the resume is written in English, your revisions must also be in English—even if the user query or instructions are in another language.

[Job Description]
{state.job_description}

[Company Summary]
{state.company_summary}

[Full Resume]
{state.resume}

[Selected Resume Section to Improve]
{state.user_resume}
"""
    model = ChatOpenAI(model=MODEL, temperature=0, api_key=OPENAI_API_KEY)

    async with MultiServerMCPClient(
        # {
        #     "github-search": {
        #         "url": "https://server.smithery.ai/@vaebe/github-search",
        #         "config": {"GithubToken": os.getenv("GITHUB_TOKEN")},
        #         "api_key": os.getenv("SMITHERY_API_KEY"),
        #     }
        # }
    ) as client:
        agent = create_react_agent(model, client.get_tools())

        messages = [SystemMessage(content=system_message), *state.messages]

        response = cast(AIMessage, await agent.ainvoke({"messages": messages}))
    return {"messages": [response["messages"][-1]], "agent_name": "suggestion_agent"}
