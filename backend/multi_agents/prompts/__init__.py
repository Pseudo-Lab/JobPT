"""
Multi-Agent Prompts 패키지

각 agent의 시스템 프롬프트를 관리합니다.
"""

from .supervisor_prompt import get_supervisor_prompt
from .summary_prompt import get_summary_prompt
from .suggestion_prompt import get_suggestion_prompt

__all__ = [
    "get_supervisor_prompt",
    "get_summary_prompt",
    "get_suggestion_prompt",
]

