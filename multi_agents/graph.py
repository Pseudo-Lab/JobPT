from states.states import State
from agent.summary_agent import summary_agent
from agent.suggestion_agent import suggest_agent
from agent.supervisor_agent import router, refine_answer
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
import asyncio


async def create_graph():
    builder = StateGraph(State)
    # Node 추가
    builder.add_node("supervisor", router)
    builder.add_node("summary_agent", summary_agent)
    builder.add_node("suggestion_agent", suggest_agent)
    builder.add_node("refine_answer", refine_answer)

    # Start → Supervisor
    builder.add_edge("__start__", "supervisor")

    # Supervisor가 유저 입력 보고 결정
    def route_supervisor(state: State):
        import json

        msg = state.messages[-1].content
        try:
            if isinstance(msg, str) and msg.strip().startswith("{"):
                seq = json.loads(msg).get("sequence", "")
            else:
                seq = msg
        except Exception:
            seq = msg
        if seq not in {"summary", "suggestion", "summary_suggestion", "END"}:
            seq = "END"
        state.route_decision = seq
        return seq

    builder.add_conditional_edges(
        source="supervisor",
        path=route_supervisor,
        path_map={
            "summary": "summary_agent",
            "suggestion": "suggestion_agent",
            "summary_suggestion": "summary_agent",
            "END": "refine_answer",  # END도 refine_answer로
        },
    )

    def route_after_summary(state: State):
        if state.route_decision == "summary_suggestion":
            return "suggestion_agent"
        else:
            return "refine_answer"

    builder.add_conditional_edges(
        source="summary_agent",
        path=route_after_summary,
        path_map={
            "suggestion_agent": "suggestion_agent",
            "refine_answer": "refine_answer",
        },
    )

    # suggestion_agent 끝나고 refine_answer로
    builder.add_edge("suggestion_agent", "refine_answer")
    # refine_answer 끝나고 항상 종료
    builder.add_edge("refine_answer", "__end__")

    return builder.compile()


async def main():
    graph = await create_graph()
    test_cases = [
        {"desc": "END", "messages": "Hi", "user_resume": ""},
        {
            "desc": "summary",
            "messages": "Summary this company",
            "user_resume": "Acme Corp is a global leader in financial technology, providing innovative payment solutions and digital banking platforms to millions of users worldwide. Founded in 2001, Acme has offices in 20 countries and is recognized for its strong commitment to security and customer service.",
            "job_description": ""
        },
        {
            "desc": "summary_suggestion",
            "messages": "Suggest this resume with company information",
            "user_resume": "Experienced software engineer with a demonstrated history of working in the fintech industry. Skilled in Python, machine learning, and cloud infrastructure. Passionate about building scalable solutions.",
        },
        {
            "desc": "suggestion",
            "messages": "Suggest this resume",
            "user_resume": "Creative marketing specialist with 5+ years of experience in digital campaigns, brand strategy, and content creation. Proven track record of increasing engagement and conversion rates.",
        },
    ]
    for case in test_cases:
        print(f"\n==== {case['desc']} CASE ====")
        state = {"messages": case["messages"], "user_resume": case["user_resume"]}
        result = await graph.ainvoke(state)
        print(result)
        if "messages" in result and len(result["messages"]) > 0:
            print(" -", result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
