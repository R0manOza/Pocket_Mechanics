"""Lab 7 — AgentState and approval helpers."""

import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parents[1] / "Backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from agent.state import (
    approval_required_for_request,
    initial_state_from_session,
)


class TestAgentState:
    def test_approval_not_required_for_general_question(self):
        assert approval_required_for_request("What is a serpentine belt?") is False

    def test_approval_required_for_repair_procedure(self):
        assert approval_required_for_request("How do I replace the serpentine belt step by step?") is True

    def test_initial_state_from_session(self):
        messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
        state = initial_state_from_session(
            "sess-1",
            "How to replace brake pads?",
            messages,
            vehicle_context="2012 Honda Civic",
            timeout_ms=25_000,
        )
        assert state.session_id == "sess-1"
        assert state.vehicle_context == "2012 Honda Civic"
        assert state.approval_required is True
        assert state.approved is False
        assert state.timeout_ms == 25_000
        assert len(state.messages) == 2
