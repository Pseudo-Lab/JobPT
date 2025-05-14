from states.states import State
from agent.summary_agent import summary_agent
from agent.suggestion_agent import suggest_agent
from agent.supervisor_minah import supervisor_node, refine_answer
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
import asyncio

from langchain_teddynote import logging

# 프로젝트 이름을 입력합니다.
logging.langsmith("JobPT-Agents")

async def create_graph():
    builder = StateGraph(State)
    # Node 추가
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("summary_agent", summary_agent)
    builder.add_node("suggestion_agent", suggest_agent)
    builder.add_node("refine_answer", refine_answer)

    # Start → Supervisor
    builder.add_edge("__start__", "supervisor")
    builder.add_edge("summary_agent", "supervisor")
    builder.add_edge("suggestion_agent", "supervisor")

    # supervisor는 그래프 상태의 "next" 필드를 채워서 노드로 라우팅하거나 종료한다
    builder.add_conditional_edges("supervisor", lambda state: state.next)

    # refine_answer에서 종료
    builder.add_edge("refine_answer", "__end__")

    return builder.compile()


async def main():
    graph = await create_graph()

    test_cases = [
        {"desc": "END", "messages": "Hi", "user_resume": ""},
        {
            "desc": "summary",
            "messages": "Summary Intel company",
            "user_resume": "Acme Corp is a global leader in financial technology, providing innovative payment solutions and digital banking platforms to millions of users worldwide. Founded in 2001, Acme has offices in 20 countries and is recognized for its strong commitment to security and customer service.",
            "job_description": ""
        },
        {
            "desc": "summary_suggestion",
            "messages": "Suggest this resume with Intel company information",
            "user_resume": "Experienced software engineer with a demonstrated history of working in the fintech industry. Skilled in Python, machine learning, and cloud infrastructure. Passionate about building scalable solutions.",
        },
        {
            "desc": "suggestion",
            "messages": "Suggest this resume",
            "user_resume": "Creative marketing specialist with 5+ years of experience in digital campaigns, brand strategy, and content creation. Proven track record of increasing engagement and conversion rates.",
        },
    ]
    # for case in test_cases:
    case = test_cases[3]
    print(f"\n==== {case['desc']} CASE ====")
    state = {"messages": case["messages"], "user_resume": case["user_resume"]}
    result = await graph.ainvoke(state)
    
    if "messages" in result and len(result["messages"]) > 0:
        print(" -", result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
