"""
Lab 7 — two-node LangGraph proof (research → write) with optional human_review.

Maps to Pocket Mechanics capstone:
  research  ≈ gather vehicle/maintenance facts for the user request
  write     ≈ user-facing answer (stream/generate in production)
  human_review ≈ high-stakes repair steps (approval_required in AgentState)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

# Allow importing Backend/agent when run from repo root
_REPO = Path(__file__).resolve().parents[2]
_BACKEND = _REPO / "Backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from agent.state import (  # noqa: E402
    STEP_AWAIT_APPROVAL,
    STEP_DONE,
    STEP_RESEARCH,
    STEP_RESPOND,
    approval_required_for_request,
)


class GraphState(TypedDict, total=False):
    session_id: str
    user_request: str
    vehicle_context: str
    research_notes: str
    draft_answer: str
    current_step: str
    approval_required: bool
    approved: bool
    retry_count: int
    timeout_ms: int
    last_error: str | None


def research_node(state: GraphState) -> GraphState:
    vehicle = state.get("vehicle_context") or "unknown vehicle"
    request = state["user_request"]
    notes = (
        f"Research summary for session {state.get('session_id', 'local')}:\n"
        f"- Vehicle context: {vehicle}\n"
        f"- User question: {request}\n"
        f"- Checked: fluids, belts, warning lights, owner-manual verification recommended."
    )
    print(f"[node:research] step={STEP_RESEARCH} wrote {len(notes)} chars of notes")
    return {
        **state,
        "research_notes": notes,
        "current_step": STEP_RESEARCH,
        "approval_required": approval_required_for_request(request),
        "approved": not approval_required_for_request(request),
    }


def write_node(state: GraphState) -> GraphState:
    notes = state.get("research_notes", "")
    request = state["user_request"]
    draft = (
        f"Based on our research:\n{notes}\n\n"
        f"Answer for you: For '{request}', start with the owner's manual and a visual "
        "inspection. Pocket Mechanics can explain parts from a photo — verify torque "
        "specs and safety steps with a qualified mechanic before working under the car."
    )
    print(f"[node:write] step={STEP_RESPOND} draft length={len(draft)}")
    return {**state, "draft_answer": draft, "current_step": STEP_RESPOND}


def human_review_node(state: GraphState) -> GraphState:
    print(
        f"[node:human_review] step={STEP_AWAIT_APPROVAL} "
        f"approval_required={state.get('approval_required')} approved={state.get('approved')}"
    )
    return {
        **state,
        "current_step": STEP_AWAIT_APPROVAL,
        "draft_answer": (
            state.get("draft_answer", "")
            + "\n\n[Human review required before sending procedural repair steps to the user.]"
        ),
    }


def route_after_write(state: GraphState) -> Literal["human_review", "end"]:
    if state.get("approval_required") and not state.get("approved"):
        return "human_review"
    return "end"


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("research", research_node)
    graph.add_node("write", write_node)
    graph.add_node("human_review", human_review_node)
    graph.set_entry_point("research")
    graph.add_edge("research", "write")
    graph.add_conditional_edges(
        "write",
        route_after_write,
        {"human_review": "human_review", "end": END},
    )
    graph.add_edge("human_review", END)
    return graph.compile()


def run_demo(user_request: str, *, vehicle_context: str = "", approved: bool = False) -> GraphState:
    app = build_graph()
    initial: GraphState = {
        "session_id": "langgraph-demo",
        "user_request": user_request,
        "vehicle_context": vehicle_context,
        "retry_count": 0,
        "timeout_ms": 30_000,
        "approved": approved,
        "current_step": "idle",
    }
    print(f"[graph] start request={user_request!r}")
    final = app.invoke(initial)
    final["current_step"] = STEP_DONE
    print(f"[graph] end step={final.get('current_step')} approval_required={final.get('approval_required')}")
    return final
