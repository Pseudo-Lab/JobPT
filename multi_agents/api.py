from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from states.states import get_session_state, end_session, add_user_input_to_state, add_assistant_response_to_state
from graph import create_graph

app = FastAPI()

from langfuse import Langfuse
from langfuse.callback import CallbackHandler

# langfuse = Langfuse(
#     secret_key="sk-lf-f2495882-bceb-4b46-ac59-65da8dd8b251", public_key="pk-lf-ce2e725b-703f-450c-a734-1b8a9274b9e1", host="https://cloud.langfuse.com"
# )


langfuse_handler = CallbackHandler(
    public_key="pk-lf-ce2e725b-703f-450c-a734-1b8a9274b9e1", secret_key="sk-lf-f2495882-bceb-4b46-ac59-65da8dd8b251", host="https://cloud.langfuse.com"
)


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    session_id = data["session_id"]
    user_input = data["messages"]

    state = get_session_state(
        session_id,
        agent_name=data.get("agent_name", ""),
        job_description=data.get("job_description", ""),
        resume=data.get("resume", ""),
        company_summary=data.get("company_summary", ""),
        user_resume=data.get("user_resume", ""),
        route_decision=data.get("route_decision", ""),
    )
    add_user_input_to_state(state, user_input)
    graph = await create_graph()
    result = await graph.ainvoke(state, config={"callbacks": [langfuse_handler]})
    answer = result["messages"][-1].content
    add_assistant_response_to_state(state, answer)
    return JSONResponse({"answer": answer, "session_id": session_id})


@app.post("/end_session")
async def end_chat(request: Request):
    data = await request.json()
    session_id = data["session_id"]
    end_session(session_id)
    return JSONResponse({"message": "세션 종료됨"})


if __name__ == "__main__":
    # uvicorn으로 서버 실행
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
