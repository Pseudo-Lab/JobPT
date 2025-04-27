from states.states import State
from agent.summary_agent import summary_agent
from agent.suggestion_agent import suggest_agent
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
import asyncio

async def create_graph():
    
    builder = StateGraph(State)
    builder.add_node("summary_agent", summary_agent)
    builder.add_node("suggestion_agent", suggest_agent)

    builder.add_edge("__start__", "summary_agent")
    builder.add_edge("summary_agent", "suggestion_agent")
    builder.add_edge("suggestion_agent", "__end__")

    graph = builder.compile()

    return graph

async def main():
    graph = await create_graph()
    query = "The company name is Intel"

    result = await graph.ainvoke({"messages": [HumanMessage(content=query)]})
    print(result)
    
if __name__ == "__main__":
    asyncio.run(main())