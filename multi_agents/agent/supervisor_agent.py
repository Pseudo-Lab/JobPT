from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv
from dataclasses import dataclass, field
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, AnyMessage
from langgraph.graph import StateGraph, add_messages
from typing_extensions import Annotated
from typing import Dict, List, cast, Annotated, Sequence
import os
import json

load_dotenv()
MODEL = "gpt-4.1-mini"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI()


@dataclass
class State:
    messages: Annotated[Sequence[AnyMessage], add_messages] = field(default_factory=list)
    user_input: str = field(default="")
    user_text: str = field(default="")
    agent_outputs: str = field(default="")


async def router(state: State):
    model = ChatOpenAI(model=MODEL, temperature=0, api_key=OPENAI_API_KEY)

    async with MultiServerMCPClient() as client:
        agent = create_react_agent(model, client.get_tools())

        system_message = """
user_input: {user_input}
user_text: {user_text}
---
This system uses a Summary Agent and a Suggestion Agent to help improve resumes.

Summary Agent: Finds and summarizes company information related to the job description the user has provided.
Suggestion Agent: Based on the user's specified part of the resume and the summarized company information, it generates concrete improvement suggestions.

Please select one of the following agent execution sequences and output it in a single line (choose exactly one of the options below):

1. END: When the input is a simple question that does not require the Summary or Suggestion Agents, or when user_text is empty.
2. summary: When only the Summary Agent is needed.
3. summary_suggestion: When the user wants to improve their resume using both the Summary and Suggestion Agents.
4. suggestion: When only the Suggestion Agent is needed, without requiring company summary information.

For each request, output the result in JSON format.
Example output:
{{
    sequence: "END"
}}
"""
        system_message = system_message.format(user_input=state.user_input, user_text=state.user_text)

        messages = [SystemMessage(content=system_message), *state.messages]

        response = cast(AIMessage, await agent.ainvoke({"messages": messages}))
        print(response)

        result = response["messages"][-1].content
        print("test")
        print(result)
        import re

        result = re.sub(r"(\w+):", r'"\1":', result)
        print("test2")
        response["messages"][-1].content = json.loads(result).get("sequence")
        print(response)
        return {"messages": [response["messages"][-1]]}


async def refine_answer(state: State):
    model = ChatOpenAI(model=MODEL, temperature=0, api_key=OPENAI_API_KEY)

    async with MultiServerMCPClient() as client:
        agent = create_react_agent(model, client.get_tools())
        system_message = f"""
Below are the user input and the results from each agent.
User Input: {state.user_input}
Agent Outputs: {state.agent_outputs}
Based on all the provided information, write a response that is concise, clear, and focuses only on the key points for the user.
"""
        messages = [SystemMessage(content=system_message), *state.messages]

        response = cast(AIMessage, await agent.ainvoke({"messages": messages}))

        return {"messages": [response["messages"][-1]]}


# # supervisor 실행 예시
# def supervisor_run(message):
#     supervisor = SupervisorAgent()
#     user_input = message["user_input"]
#     user_text = message["user_text"]
#     # 1. route로 시퀀스 결정
#     sequence = supervisor.route(state)
#     print(sequence)

#     state = defaultdict(str)  # agent_outputs를 담을 state
#     # 2. 각 agent 실행 결과를 state에 저장
#     for agent_type in sequence:
#         if agent_type == "END":
#             break

#         # ==================== 실제 Agent 실행 시작 =======================

#         # ==================== 실제 Agent 실행 종료 =======================

#         output = f"{agent_type} 실행 결과"  # 실제로는 해당 agent 함수 호출
#         state[agent_type] = output
#     # 3. refine_answer 호출 (state를 agent_outputs로 전달)
#     final_answer = supervisor.refine_answer(user_input, state)
#     return final_answer


# if __name__ == "__main__":
#     # message 예시
#     messages = [
#         {"user_input": "내 이력서에 대한 구체적인 개선점을 알려줘.", "user_text": ""},
#         {"user_input": "내 이력서에 대해 관련한 회사 정보와 함께 추가될 내용을 추천해줘.", "user_text": ""},
#         {"user_input": "안녕하세요", "user_text": ""},
#     ]
#     for message in messages:
#         result = supervisor_run(message)
#         print(result)
