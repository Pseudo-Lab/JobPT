from typing import Annotated, TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage


class State(TypedDict):
    """
    LangGraph State 정의 (TypedDict 사용)
    - messages: add_messages reducer를 사용하여 자동으로 메시지 누적
    - 나머지 필드들은 일반 타입으로 정의
    """
    messages: Annotated[list[AnyMessage], add_messages]
    job_description: str
    resume: str  # 유저 전체 resume
    # company_summary: str
    # user_resume: str  # 유저가 선택한 resume 부분
    # route_decision: str
    company_name: str
    # Supervisor Loop 패턴용 필드
    next_agent: str  # "summary" | "suggestion" | "FINISH"
    agent_outputs: dict  # {"summary": "...", "suggestion": "..."}
    final_answer: str
    github_url: str
    blog_url: str
