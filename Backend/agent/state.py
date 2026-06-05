"""
Lab 7 — explicit AgentState for Pocket Mechanics.

Single-agent architecture: one multimodal assistant with optional MCP tool;
state is shared across stream turns and the LangGraph proof in orchestration/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Steps used in production stream + LangGraph mini-build
STEP_IDLE = "idle"
STEP_LOAD_SESSION = "load_session"
STEP_RESEARCH = "research"
STEP_GENERATE = "generate"
STEP_AWAIT_APPROVAL = "await_approval"
STEP_RESPOND = "respond"
STEP_DONE = "done"
STEP_ERROR = "error"

# Phrases that imply hands-on repair steps — require explicit user acknowledgment in UI
_HIGH_STAKES_MARKERS = (
    "step by step repair",
    "step-by-step",
    "how do i replace",
    "how to replace",
    "how i replace",
    "replace them",
    "replace the ",
    "replace my ",
    "replace a ",
    "instructions to replace",
    "help me with instructions",
    "remove the ",
    "disconnect the battery",
    "jack up",
    "under the car",
    "torque spec",
    "drain the ",
    "bleed the ",
    "install the ",
    "change the headlight",
    "change the bulb",
    "replace the bulb",
    "replace the light",
)


@dataclass
class AgentState:
    session_id: str
    user_request: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    current_step: str = STEP_IDLE
    approval_required: bool = False
    approved: bool = False
    retry_count: int = 0
    timeout_ms: int = 30_000
    last_error: str | None = None
    # Domain field — car context for maintenance answers
    vehicle_context: str = ""
    research_notes: str = ""
    draft_answer: str = ""


def approval_required_for_request(user_request: str) -> bool:
    """True when the user asks for procedural repair work (human should confirm first)."""
    lower = user_request.lower()
    return any(marker in lower for marker in _HIGH_STAKES_MARKERS)


def initial_state_from_session(
    session_id: str,
    user_request: str,
    messages: list[dict[str, Any]],
    *,
    vehicle_context: str = "",
    timeout_ms: int = 30_000,
) -> AgentState:
    return AgentState(
        session_id=session_id,
        user_request=user_request,
        messages=list(messages),
        current_step=STEP_LOAD_SESSION,
        approval_required=approval_required_for_request(user_request),
        approved=not approval_required_for_request(user_request),
        timeout_ms=timeout_ms,
        vehicle_context=vehicle_context,
    )
