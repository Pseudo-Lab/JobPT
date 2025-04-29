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
        # supervisor가 반환한 마지막 메시지에서 'sequence' 값을 추출
        import json

        msg = state.messages[-1].content
        try:
            # JSON 파싱 시도 (예: {"sequence": "summary"})
            if isinstance(msg, str) and msg.strip().startswith("{"):
                seq = json.loads(msg).get("sequence", "")
            else:
                seq = msg
        except Exception:
            seq = msg
        # 만약 분기 조건에 없는 값이면 "END"로 fallback
        if seq not in {"summary", "suggestion", "summary_suggestion", "END"}:
            seq = "END"
        state.route_decision = seq  # state에 저장(필수)
        return seq

    # Supervisor 분기
    builder.add_conditional_edges(
        source="supervisor",
        path=route_supervisor,
        path_map={
            "summary": "summary_agent",
            "suggestion": "suggestion_agent",
            "summary_suggestion": "summary_agent",  # 일단 summary로 가고, summary 끝나면 suggestion으로
            "END": "__end__",
        },
    )

    # summary_agent 끝나고 next
    def route_after_summary(state: State):
        if state.route_decision == "summary_suggestion":
            return "suggestion_agent"
        else:
            return "__end__"

    builder.add_conditional_edges(
        source="summary_agent",
        path=route_after_summary,
        path_map={
            "suggestion_agent": "suggestion_agent",
            "__end__": "__end__",
        },
    )

    # Compile
    graph = builder.compile()

    return graph


async def main():
    graph = await create_graph()
    query = "The company name is Intel"

    result = await graph.ainvoke({"messages": [HumanMessage(content=query)]})
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
