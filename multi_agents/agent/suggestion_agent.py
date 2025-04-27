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

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4.1-mini"


@dataclass
class State:
    messages: Annotated[Sequence[AnyMessage], add_messages] = field(default_factory=list)
    summary: str = field(default="")
    user_text: str = field(default="")


async def suggest(state: State):
    """
    이력서와 요약 정보를 바탕으로 개선 제안 생성
    """
    # OpenAI API 사용
    system_message = f"""
당신은 이력서 개선을 도와주는 전문가입니다.
아래 이력서와 직무(회사) 요약 정보를 참고하여, 다음 조건에 따라 3~5개의 구체적이고 실질적인 개선 제안을 생성하세요.

[조건]
- 각 제안은 반드시 한 줄로 명확하게 작성하세요.
- 이력서와 직무 요약을 모두 반영하세요.
- 직무 요구사항에 부합하는 경험, 기술, 성과, 프로젝트, 리더십, 최신 트렌드 반영 등 다양한 관점에서 제안하세요.
- 실질적으로 이력서에 추가하거나 개선하면 좋은 점을 구체적으로 제시하세요.

[이력서]
{state.user_text}

[직무 요약]
{state.summary}
"""
    model = ChatOpenAI(model=MODEL, temperature=0, api_key=OPENAI_API_KEY)

    async with MultiServerMCPClient() as client:
        agent = create_react_agent(model, client.get_tools())

        messages = [SystemMessage(content=system_message), *state.messages]

        response = cast(AIMessage, await agent.ainvoke({"messages": messages}))

    return {"messages": [response["messages"][-1]]}


async def main(query: str):

    builder = StateGraph(State)
    builder.add_node("call_model", suggest)

    builder.add_edge("__start__", "call_model")
    builder.add_edge("call_model", "__end__")

    graph = builder.compile()

    result = await graph.ainvoke({"messages": [HumanMessage(content=query)]})
    return result


if __name__ == "__main__":
    query = "The company name is Intel"

    summary_result = asyncio.run(main(query))
    print(summary_result)
