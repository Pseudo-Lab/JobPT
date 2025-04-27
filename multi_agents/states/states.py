from dataclasses import dataclass, field
from typing import Annotated, Sequence
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage

@dataclass
class State:
    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
            default_factory=list
    )
    agent_name: str = field(default="")
    job_description: str = field(default="")
    resume: str = field(default="")
    company_summary: str = field(default="")
    user_resume: str = field(default="")
