from typing import Literal
from typing_extensions import TypedDict
from states.states import State
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage
from typing import cast

members = ["summary_agent", "suggestion_agent"]

# system_prompt = (
#     f"""You are a supervisor tasked with managing a conversation between the following workers: {members}.  
# Given the following user request, respond with the appropriate worker to act next.  
# Each worker will perform a task and respond with their results and status. When all tasks are complete, respond with FINISH."""
# )

# system_prompt = f"""
# You are a supervisor tasked with managing a conversation between the following workers: {members}.  
# Given the following user request, determine if any worker is needed.  
# - If the request can be answered without involving any worker, respond with FINISH.  
# - Otherwise, select the appropriate worker to act next.  
# Each worker will perform a task and respond with their results and status. When all tasks are complete, respond with FINISH."""

# system_prompt = """
# user_input: {user_input}
# agent_outputs: {agent_outputs}
# ---
# You are a supervisor tasked with managing a conversation between the following workers: {members}.

# Given the following user request and any previous responses, decide whether further action is required.  
# - If the user's question has already been sufficiently answered or no additional work is needed, respond with FINISH.  
# - Otherwise, select the appropriate worker to act next.  
# Each worker will perform a task and respond with their results and status. When all tasks are complete or no further steps are needed, respond with FINISH.
# """

system_prompt = """
user_query: {user_query}
agent_outputs: {agent_outputs}
---
This system uses a Summary Agent and a Suggestion Agent to help improve resumes.

You are a supervisor tasked with managing a conversation between the following workers: {members}.

summary_agent: Finds and summarizes company information related to the job description the user has provided.
suggestion_agent: Based on the user's specified part of the resume and the summarized company information, it generates concrete improvement suggestions.

Please select the appropriate agent to act next and output it in a single line (choose exactly one of the options below):

1. FINISH: When the input is a simple question that does not require the Summary or Suggestion Agents, or when agent_outputs contains sufficient information to answer the user_query.
2. summary_agent: When the Summary Agent is needed.
3. suggestion_agent: When the Suggestion Agent is needed.  
"""

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    
    next: Literal["summary_agent", "suggestion_agent", "FINISH"]

def supervisor_node(state: State) -> State:
    llm = ChatOpenAI(model="gpt-4o") # gpt-4o-mini로 하면 잘 안된다.

    # Collect all AIMessage contents
    agent_outputs = "\n".join([
        msg.content for msg in state.messages 
        if isinstance(msg, AIMessage)
    ])

    formatted_prompt = system_prompt.format(
        user_query=state.messages[0].content,
        agent_outputs=agent_outputs,
        members=members
    )

    messages = [
        {"role": "system", "content": formatted_prompt},
    ]
    response = llm.with_structured_output(Router).invoke(messages)
    next_ = response["next"]
    if next_ == "FINISH":
        next_ = "refine_answer"

    return {"next": next_}

def refine_answer(state: State) -> State:
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    system_template = """
    Below are the user input and the results from each agent.
    User Input: {user_input}
    Agent Outputs: {agent_outputs}
    Based on all the provided information, write a response that is concise, clear, and focuses only on the key points for the user.
    """

    prompt = PromptTemplate.from_template(system_template)

    chain = prompt | model | StrOutputParser()
    answer = chain.invoke({"user_input": state.messages[0].content, "agent_outputs": state.messages[-1].content})
    print(answer)
    return {"messages": [AIMessage(content=answer)]}
