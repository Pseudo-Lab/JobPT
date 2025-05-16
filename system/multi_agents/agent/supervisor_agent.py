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
from multi_agents.states.states import State
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

import os
import json
import re
from configs import *

client = OpenAI()


async def router(state: State):
    model = ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)

    async with MultiServerMCPClient() as client:
        agent = create_react_agent(model, client.get_tools())

    system_message = """
user_input: {user_input}
user_resume: {user_resume}
---
This system uses a Summary Agent and a Suggestion Agent to help improve resumes.

Summary Agent: Finds and summarizes company information related to the job description the user has provided.
Suggestion Agent: Based on the user's specified part of the resume and the summarized company information, it generates concrete improvement suggestions.

Please select one of the following agent execution sequences and output it in a single line (choose exactly one of the options below):

1. END: When the input is a simple question that does not require the Summary or Suggestion Agents, or when user_resume is empty.
2. summary: When only the Summary Agent is needed.
3. summary_suggestion: When the user wants to improve their resume using both the Summary and Suggestion Agents.
4. suggestion: When only the Suggestion Agent is needed, without requiring company summary information.

For each request, output the result in JSON format.
Only return key of 'sequence', don't return any other key.
Example each output:
{{
    sequence: "END"
}}
{{
    sequence: "summary"
}}
{{
    sequence: "summary_suggestion"
}}
{{
    sequence: "suggestion"
}}
"""
    system_message = system_message.format(user_input=state.messages, user_resume=state.user_resume)

    messages = [SystemMessage(content=system_message), *state.messages]

    response = cast(AIMessage, await agent.ainvoke({"messages": messages}))

    result = response["messages"][-1].content
    print("=============router=============")
    print(result)
    result = re.sub(r"(\w+):", r'"\1":', result)
    state.route_decision = json.loads(result).get("sequence")
    response["messages"][-1].content = json.loads(result).get("sequence")
    return {"messages": [response["messages"][-1]]}


def refine_answer(state: State) -> State:
    model = ChatOpenAI(model="gpt-4.1-mini", temperature=0, api_key=OPENAI_API_KEY)

    system_message = """
You are an assistant helping to finalize a user-facing response.

Below are the original user input and the assistant's draft reply:
- User Input: {user_input}
- Assistant Draft Response: {assistant_response}

if Assistant Draft Response is 'END', focus on user input and generate answer spontaneously.

Your task is to **lightly polish the draft** without changing its meaning, tone, or structure. Keep all key details intact. 
Focus only on improving clarity, grammar, or flow if necessary.

Do NOT remove important information or rephrase in a way that could alter the intent.

If the assistant's reply is already clear and appropriate, return it unchanged.
"""
    prompt = PromptTemplate.from_template(system_message)
    chain = prompt | model | StrOutputParser()
    answer = chain.invoke({"user_input": state.messages[0].content, "assistant_response": state.messages[-1].content})
    print(answer)
    return {"messages": [AIMessage(content=answer)]}
