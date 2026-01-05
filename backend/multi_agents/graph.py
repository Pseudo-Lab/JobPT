from multi_agents.states.states import State, get_session_state, end_session
from multi_agents.agent.summary_agent import summary_agent
from multi_agents.agent.suggestion_agent import suggest_agent
from multi_agents.agent.supervisor_agent import supervisor
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
import asyncio


async def create_graph(state: State):
    """
    Supervisor Loop 패턴의 Graph 생성

    Flow:
    START → Supervisor ─┬─ "summary" ──────→ summary_agent ──┐
                        ├─ "suggestion" ───→ suggestion_agent─┤
                        └─ "FINISH" ───────→ END              │
                             ↑                                │
                             └────────────────────────────────┘
    """
    builder = StateGraph(State)

    # Node 추가
    builder.add_node("supervisor", supervisor)
    builder.add_node("summary_agent", summary_agent)
    builder.add_node("suggestion_agent", suggest_agent)

    # Start → Supervisor
    builder.add_edge("__start__", "supervisor")

    # Supervisor → 조건부 라우팅
    def route_from_supervisor(state: State) -> str:
        """Supervisor의 결정에 따라 다음 노드 선택"""
        next_agent = state.next_agent
        print(f"=============route_from_supervisor: {next_agent}=============")

        if next_agent == "FINISH":
            return "__end__"
        elif next_agent == "summary":
            return "summary_agent"
        elif next_agent == "suggestion":
            return "suggestion_agent"
        else:
            # 알 수 없는 값은 종료
            return "__end__"

    builder.add_conditional_edges(
        source="supervisor",
        path=route_from_supervisor,
    )

    # Agent 실행 후 → Supervisor로 복귀 (Loop)
    builder.add_edge("summary_agent", "supervisor")
    builder.add_edge("suggestion_agent", "supervisor")

    return builder.compile(), state
