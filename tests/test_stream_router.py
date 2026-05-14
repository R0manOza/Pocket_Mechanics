"""
Integration tests for stream router (SSE streaming endpoint).
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestStreamChatEndpoint:
    """Test /api/ai/stream endpoint with SSE streaming."""

    def test_stream_with_valid_request_openrouter(
    self, reset_llm_service, reset_session_service, temp_logs_dir, mock_openrouter_stream
):
        """Test successful streaming chat via OpenRouter."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openrouter_stream

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.post(
                "/api/ai/stream",
                json={
                    "message": "What is a serpentine belt?",
                    "session_id": "test-session-1",
                },
            )

            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

            # Parse SSE stream
            events = []
            done_seen = False

            for block in response.text.strip().split("\n\n"):
                if not block.startswith("data: "):
                    continue

                payload = block.removeprefix("data: ").strip()

                if payload == "[DONE]":
                    done_seen = True
                    continue

                events.append(json.loads(payload))

            # Verify we got token events
            token_events = [e for e in events if "token" in e]
            assert len(token_events) > 0
            full_text = "".join(e["token"] for e in token_events)
            assert full_text == "Hello from OpenRouter!"

            # Verify we got usage event
            usage_events = [e for e in events if "usage" in e]
            assert len(usage_events) > 0
            usage = usage_events[0]["usage"]
            assert usage["input_tokens"] == 12
            assert usage["output_tokens"] == 25
            assert "latency_ms" in usage

            # Verify done marker
            assert done_seen is True

    def test_stream_creates_session(self, reset_session_service, temp_logs_dir, mock_openrouter_stream):
        """Test that stream creates session with system message."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openrouter_stream

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient
            from services.session_service import load_session

            client = TestClient(app)
            response = client.post(
                "/api/ai/stream",
                json={
                    "message": "First message",
                    "session_id": "session-123",
                },
            )

            # Consume the stream
            _ = response.text

            # Verify session was created and persisted
            session = load_session("session-123")
            assert len(session) > 0
            assert session[0]["role"] == "system"
            assert "Pocket Mechanics" in session[0]["content"]

    def test_stream_preserves_user_message(self, reset_session_service, temp_logs_dir, mock_openrouter_stream):
        """Test that stream persists user message to session."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openrouter_stream

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient
            from services.session_service import load_session

            client = TestClient(app)
            user_msg = "What is brake fluid?"
            response = client.post(
                "/api/ai/stream",
                json={
                    "message": user_msg,
                    "session_id": "session-124",
                },
            )

            # Consume stream
            _ = response.text

            session = load_session("session-124")
            user_messages = [m for m in session if m["role"] == "user"]
            assert len(user_messages) > 0
            assert user_messages[-1]["content"] == user_msg

    def test_stream_saves_assistant_response(self, reset_session_service, temp_logs_dir, mock_openrouter_stream):
        """Test that stream saves assistant response to session."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openrouter_stream

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient
            from services.session_service import load_session

            client = TestClient(app)
            response = client.post(
                "/api/ai/stream",
                json={
                    "message": "First message",
                    "session_id": "session-125",
                },
            )

            # Consume stream
            _ = response.text

            session = load_session("session-125")
            assistant_messages = [m for m in session if m["role"] == "assistant"]
            assert len(assistant_messages) > 0
            assert assistant_messages[-1]["content"] == "Hello from OpenRouter!"

    def test_stream_with_custom_system_prompt(
        self, reset_session_service, temp_logs_dir, mock_openrouter_stream
    ):
        """Test stream with custom system prompt."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openrouter_stream

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            custom_system = "You are a technical mechanic expert."
            response = client.post(
                "/api/ai/stream",
                json={
                    "message": "Explain transmission",
                    "session_id": "session-126",
                    "system": custom_system,
                },
            )

            assert response.status_code == 200
            # Verify custom system was passed
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]["messages"]
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == custom_system

    def test_stream_with_model_override(self, reset_llm_service, reset_session_service, temp_logs_dir):
        """Test stream with model override."""
        mock_chunk_1 = MagicMock()
        mock_chunk_1.choices = [MagicMock(delta=MagicMock(content="Hi"))]
        mock_chunk_1.usage = None

        mock_chunk_2 = MagicMock()
        mock_chunk_2.choices = [MagicMock(delta=MagicMock(content=None))]
        final_usage = MagicMock()
        final_usage.prompt_tokens = 5
        final_usage.completion_tokens = 10
        mock_chunk_2.usage = final_usage

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [mock_chunk_1, mock_chunk_2]

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.post(
                "/api/ai/stream",
                json={
                    "message": "Test",
                    "session_id": "session-127",
                    "model": "openai/gpt-4o",
                },
            )

            assert response.status_code == 200
            # Verify model was used
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "openai/gpt-4o"

    def test_stream_multi_turn_conversation(
        self, reset_session_service, temp_logs_dir, mock_openrouter_stream
    ):
        """Test multi-turn streaming conversation."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openrouter_stream

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient
            from services.session_service import load_session

            client = TestClient(app)

            # First turn
            response1 = client.post(
                "/api/ai/stream",
                json={
                    "message": "What are brakes?",
                    "session_id": "conv-1",
                },
            )
            _ = response1.text

            session1 = load_session("conv-1")
            assert len(session1) == 3  # system, user, assistant

            # Second turn
            response2 = client.post(
                "/api/ai/stream",
                json={
                    "message": "How do I maintain them?",
                    "session_id": "conv-1",
                },
            )
            _ = response2.text

            session2 = load_session("conv-1")
            # Should preserve previous messages
            assert len(session2) > 3
            user_messages = [m for m in session2 if m["role"] == "user"]
            assert len(user_messages) == 2

    def test_stream_with_missing_session_id(self, app_with_mocks):
        """Test stream with missing session_id."""
        response = app_with_mocks.post(
            "/api/ai/stream",
            json={"message": "Test"},
        )

        assert response.status_code == 422

    def test_stream_with_empty_message(self, app_with_mocks):
        """Test stream with empty message and no images."""
        response = app_with_mocks.post(
            "/api/ai/stream",
            json={"message": "", "session_id": "session-1"},
        )

        assert response.status_code == 422

    def test_stream_image_only_sends_multimodal_user_message(
        self, reset_session_service, temp_logs_dir, mock_openrouter_stream
    ):
        """Vision: image-only stream builds OpenAI-style multimodal user content."""
        tiny = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openrouter_stream

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient
            from services.session_service import load_session

            client = TestClient(app)
            response = client.post(
                "/api/ai/stream",
                json={"message": "", "session_id": "vision-session", "images": [tiny]},
            )
            assert response.status_code == 200
            _ = response.text
            mock_client.chat.completions.create.assert_called()
            msgs = mock_client.chat.completions.create.call_args[1]["messages"]
            user_msgs = [m for m in msgs if m["role"] == "user"]
            assert user_msgs
            assert isinstance(user_msgs[-1]["content"], list)
            saved = load_session("vision-session")
            user_turns = [m for m in saved if m["role"] == "user"]
            assert user_turns
            assert isinstance(user_turns[-1]["content"], list)

    def test_stream_error_handling_during_stream(
        self, reset_llm_service, reset_session_service, temp_logs_dir
    ):
        """Test error handling during stream."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("Stream failed")

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.post(
                "/api/ai/stream",
                json={
                    "message": "Test",
                    "session_id": "error-session",
                },
            )

            assert response.status_code == 200  # SSE always returns 200
            text = response.text
            # Should contain error marker
            assert "error" in text.lower()

    def test_stream_cache_control_headers(self, app_with_mocks, mock_openrouter_client):
        """Test that SSE response has correct cache control headers."""
        mock_openrouter_client.chat.completions.create.return_value = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="test"))], usage=None),
            MagicMock(
                choices=[MagicMock(delta=MagicMock(content=None))],
                usage=MagicMock(prompt_tokens=5, completion_tokens=10),
            ),
        ]

        response = app_with_mocks.post(
            "/api/ai/stream",
            json={"message": "Test", "session_id": "cache-test"},
        )

        assert response.headers["Cache-Control"] == "no-cache"
        assert response.headers["X-Accel-Buffering"] == "no"

    def test_stream_session_memory_trimming(
        self, reset_session_service, temp_logs_dir, mock_openrouter_stream
    ):
        """Test that long sessions are trimmed to MAX_TURNS."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openrouter_stream

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient
            from services.session_service import load_session, MAX_TURNS

            client = TestClient(app)

            # Create many turns to exceed MAX_TURNS
            for i in range(MAX_TURNS + 5):
                response = client.post(
                    "/api/ai/stream",
                    json={
                        "message": f"Message {i}",
                        "session_id": "trim-session",
                    },
                )
                _ = response.text

            session = load_session("trim-session")
            # Should have system message + at most MAX_TURNS * 2 other messages
            non_system = [m for m in session if m["role"] != "system"]
            assert len(non_system) <= MAX_TURNS * 2

    def test_stream_sse_format(self, reset_session_service, temp_logs_dir, mock_openrouter_stream):
        """Test that stream response is valid SSE format."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openrouter_stream

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.post(
                "/api/ai/stream",
                json={"message": "Test", "session_id": "sse-test"},
            )

            # Each event should be prefixed with "data: "
            lines = response.text.split("\n")
            data_lines = [l for l in lines if l.startswith("data: ")]
            assert len(data_lines) > 0

            # Each should be valid JSON
            for line in data_lines:
                json_str = line.replace("data: ", "").strip()
                if json_str and json_str != "[DONE]":
                    json.loads(json_str)
