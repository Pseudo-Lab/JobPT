from states.states import State
from agent.search_agent import call_model
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
import asyncio

async def create_graph():
    
    builder = StateGraph(State)
    builder.add_node("call_model", call_model)

    builder.add_edge("__start__", "call_model")
    builder.add_edge("call_model", "__end__")

    graph = builder.compile()

    return graph

async def main():
    graph = await create_graph()
    query = "The company name is Intel"

    summary_result = await graph.ainvoke({"messages": [HumanMessage(content=query)]})
    print(summary_result)

if __name__ == "__main__":
    asyncio.run(main())