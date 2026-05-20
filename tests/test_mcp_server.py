"""Lab 8 — MCP server auth, validation, and error sanitisation."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

MCP_DIR = Path(__file__).resolve().parents[1] / "mcp-server"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

from auth import extract_bearer_token, verify_bearer_token  # noqa: E402
from validated_tool import PocketMechanicsTipInput, validate_tool_input  # noqa: E402


class TestMcpAuth:
    def test_verify_rejects_wrong_token(self, monkeypatch):
        monkeypatch.setenv("MCP_SECRET_KEY", "secret-token")
        import importlib
        import auth as auth_mod

        importlib.reload(auth_mod)
        assert auth_mod.verify_bearer_token("wrong") is False
        assert auth_mod.verify_bearer_token("secret-token") is True

    def test_extract_bearer_from_authorization_header(self):
        assert extract_bearer_token({"authorization": "Bearer abc123"}) == "abc123"
        assert extract_bearer_token({"_auth_token": "direct"}) == "direct"


class TestMcpValidation:
    def test_valid_input(self):
        m = validate_tool_input(
            "ask_pocket_mechanics_tip",
            {"_auth_token": "x", "question": "What is oil?", "vehicle_hint": "2012 Civic"},
        )
        assert m.question == "What is oil?"

    def test_unknown_tool(self):
        with pytest.raises(ValueError):
            validate_tool_input("other_tool", {"question": "hi"})

    def test_missing_question_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PocketMechanicsTipInput(_auth_token="t")


@pytest.mark.asyncio
async def test_call_tool_sanitised_error(monkeypatch):
    pytest.importorskip("mcp")
    monkeypatch.setenv("MCP_SECRET_KEY", "test-secret")
    import importlib
    import server as mcp_server

    importlib.reload(mcp_server)

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.side_effect = RuntimeError("internal db path /secret")
        mock_client_cls.return_value = mock_client

        result = await mcp_server.call_tool(
            "ask_pocket_mechanics_tip",
            {"_auth_token": "test-secret", "question": "What is coolant?"},
        )
        text = result[0].text
        assert "traceback" not in text.lower()
        assert "secret" not in text.lower() or "error" in text
        payload = json.loads(text)
        assert payload.get("error") == "tool_execution_failed"
