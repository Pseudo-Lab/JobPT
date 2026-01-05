from dataclasses import dataclass, field
from typing import Annotated, Sequence
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage


@dataclass
class State:
    session_id: str = ""
    chat_history: list = field(default_factory=list)  # [{"role": "user"|"assistant", "content": str}]
    messages: Annotated[Sequence[AnyMessage], add_messages] = field(default_factory=list)
    agent_name: str = field(default="")
    job_description: str = field(default="")
    resume: str = field(default="")  # 유저 전체 resume
    user_resume: str = field(default="")  # 유저가 선택한 resume 부분
    company_name: str = field(default="")
    # 새로운 Supervisor Loop 패턴용 필드
    next_agent: str = field(default="")  # "summary" | "suggestion" | "FINISH"
    agent_outputs: dict = field(default_factory=dict)  # {"summary": "...", "suggestion": "..."}
    final_answer: str = field(default="")
    github_url: str = field(default="")
    blog_url: str = field(default="")


# 세션별 State 인스턴스를 저장하는 딕셔너리
session_states = {}


def start_session(session_id: str, **kwargs):
    """새로운 세션 시작 (State 생성, 모든 필드 초기화)"""
    # State의 모든 필드를 kwargs에서 받아서 생성
    state = State(
        session_id=session_id,
        messages=[],
        chat_history=[],
        agent_name=kwargs.get("agent_name", ""),
        job_description=kwargs.get("job_description", ""),
        resume=kwargs.get("resume", ""),
        user_resume=kwargs.get("user_resume", ""),
        company_name=kwargs.get("company_name", ""),
        next_agent=kwargs.get("next_agent", ""),
        agent_outputs=kwargs.get("agent_outputs", {}),
        final_answer=kwargs.get("final_answer", ""),
        github_url=kwargs.get("github_url", ""),
        blog_url=kwargs.get("blog_url", ""),
    )
    session_states[session_id] = state


def add_user_input_to_state(state, user_input):
    # chat_history에는 기존대로 저장
    state.chat_history.append({"role": "user", "content": user_input})
    # messages에도 HumanMessage로 누적 추가
    state.messages.append(HumanMessage(content=user_input))


def add_assistant_response_to_state(state, assistant_response):
    # chat_history에 assistant 답변 저장
    state.chat_history.append({"role": "assistant", "content": assistant_response})
    # messages에도 AIMessage로 누적 추가
    state.messages.append(AIMessage(content=assistant_response))


def get_session_state(session_id: str, **kwargs):
    """세션의 State 반환 (없으면 새로 생성, 인풋 값으로 초기화)"""
    if session_id not in session_states:
        start_session(session_id, **kwargs)
    else:
        # 기존 세션이 있어도 매 요청마다 업데이트해야 하는 필드들
        state = session_states[session_id]
        if "user_resume" in kwargs:
            state.user_resume = kwargs["user_resume"]
        if "job_description" in kwargs:
            state.job_description = kwargs["job_description"]
        if "company_name" in kwargs:
            state.company_name = kwargs["company_name"]
    return session_states[session_id]


def end_session(session_id: str):
    """세션 종료 및 멀티턴 데이터 삭제"""
    if session_id in session_states:
        del session_states[session_id]
