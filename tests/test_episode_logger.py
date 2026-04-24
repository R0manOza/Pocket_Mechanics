"""
Integration tests for episode logger (event logging and cost tracking).
"""

import json
import os

import pytest


class TestEpisodeLogger:
    """Test episode logging functionality."""

    def test_log_episode_creates_file(self, reset_session_service, temp_logs_dir):
        """Test that logging creates the episode log file."""
        from services.episode_logger import log_episode, Episode

        ep = Episode(session_id="test-session", event_type="test_event")
        result = log_episode(ep)

        assert os.path.exists(os.environ["EPISODE_LOG_PATH"])
        assert result.cost_usd >= 0

    def test_log_episode_writes_csv_header(self, reset_session_service, temp_logs_dir):
        """Test that episode log includes CSV header."""
        from services.episode_logger import log_episode, Episode

        ep = Episode(session_id="test", event_type="test")
        log_episode(ep)

        log_path = os.environ["EPISODE_LOG_PATH"]
        with open(log_path) as f:
            first_line = f.readline()
            assert "session_id" in first_line
            assert "event_type" in first_line

    def test_log_user_message(self, reset_session_service, temp_logs_dir):
        """Test logging user message event."""
        from services.episode_logger import log_user_message

        ep = log_user_message("session-123")

        assert ep.session_id == "session-123"
        assert ep.event_type == "user_message"
        assert ep.episode_id.startswith("ep_")

    def test_log_stream_end(self, reset_session_service, temp_logs_dir):
        """Test logging stream end event."""
        from services.episode_logger import log_stream_end

        ep = log_stream_end(
            session_id="session-456",
            model="google/gemini-2.5-flash",
            input_tokens=100,
            output_tokens=250,
            stream_start_ms=1000,
            stream_end_ms=2500,
        )

        assert ep.session_id == "session-456"
        assert ep.event_type == "stream_end"
        assert ep.model == "google/gemini-2.5-flash"
        assert ep.input_tokens == 100
        assert ep.output_tokens == 250
        assert ep.latency_ms == 1500

    def test_log_stream_end_with_cancellation(self, reset_session_service, temp_logs_dir):
        """Test logging cancelled stream."""
        from services.episode_logger import log_stream_end

        ep = log_stream_end(
            session_id="session",
            model="model",
            input_tokens=10,
            output_tokens=20,
            stream_start_ms=1000,
            stream_end_ms=2000,
            was_cancelled=True,
        )

        assert ep.was_cancelled is True

    def test_log_tool_call(self, reset_session_service, temp_logs_dir):
        """Test logging tool call event."""
        from services.episode_logger import log_tool_call

        ep = log_tool_call(
            session_id="session",
            tool_name="get_weather",
            arguments={"location": "New York"},
            result="Sunny, 72F",
            latency_ms=500,
            success=True,
        )

        assert ep.event_type == "tool_call"
        assert ep.tool_name == "get_weather"
        assert ep.latency_ms == 500
        assert ep.success is True
        assert json.loads(ep.arguments) == {"location": "New York"}

    def test_log_tool_call_failure(self, reset_session_service, temp_logs_dir):
        """Test logging failed tool call."""
        from services.episode_logger import log_tool_call

        ep = log_tool_call(
            session_id="session",
            tool_name="api_call",
            arguments={},
            result=None,
            latency_ms=100,
            success=False,
        )

        assert ep.success is False

    def test_log_error(self, reset_session_service, temp_logs_dir):
        """Test logging error event."""
        from services.episode_logger import log_error

        error = ValueError("Test error message")
        ep = log_error(session_id="session", error=error, context="test_context")

        assert ep.event_type == "error"
        assert ep.success is False
        assert "test_context" in ep.result_summary
        assert "Test error" in ep.result_summary

    def test_log_error_without_context(self, reset_session_service, temp_logs_dir):
        """Test logging error without context."""
        from services.episode_logger import log_error

        error = RuntimeError("API failed")
        ep = log_error(session_id="session", error=error)

        assert ep.event_type == "error"
        assert "API failed" in ep.result_summary

    def test_episode_cost_calculation(self, reset_session_service, temp_logs_dir):
        """Test that episode cost is calculated correctly."""
        from services.episode_logger import log_stream_end

        ep = log_stream_end(
            session_id="session",
            model="google/gemini-2.5-flash",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            stream_start_ms=0,
            stream_end_ms=1000,
        )

        # Flash: input 0.15, output 0.60 per M tokens
        expected_cost = 0.15 + 0.60
        assert ep.cost_usd == pytest.approx(expected_cost, rel=0.01)

    def test_episode_free_model_cost(self, reset_session_service, temp_logs_dir):
        """Test that free models have zero cost."""
        from services.episode_logger import log_stream_end

        ep = log_stream_end(
            session_id="session",
            model="meta-llama/llama-4-maverick:free",
            input_tokens=5_000_000,
            output_tokens=10_000_000,
            stream_start_ms=0,
            stream_end_ms=5000,
        )

        assert ep.cost_usd == 0.0

    def test_episode_id_uniqueness(self, reset_session_service, temp_logs_dir):
        """Test that each episode gets a unique ID."""
        from services.episode_logger import log_user_message

        ep1 = log_user_message("session")
        ep2 = log_user_message("session")

        assert ep1.episode_id != ep2.episode_id
        assert ep1.episode_id.startswith("ep_")
        assert ep2.episode_id.startswith("ep_")

    def test_episode_timestamp(self, reset_session_service, temp_logs_dir):
        """Test that episodes have timestamps."""
        from services.episode_logger import log_user_message

        ep = log_user_message("session")

        assert ep.ts is not None
        assert "T" in ep.ts  # ISO format includes T
        assert "Z" in ep.ts or "+" in ep.ts  # Has timezone

    def test_log_tool_call_result_truncation(self, reset_session_service, temp_logs_dir):
        """Test that large tool call results are truncated."""
        from services.episode_logger import log_tool_call

        large_result = "X" * 500
        ep = log_tool_call(
            session_id="session",
            tool_name="tool",
            arguments={},
            result=large_result,
            latency_ms=100,
        )

        assert len(ep.result_summary) <= 200

    def test_log_error_message_truncation(self, reset_session_service, temp_logs_dir):
        """Test that error messages are truncated."""
        from services.episode_logger import log_error

        long_error = RuntimeError("E" * 300)
        ep = log_error("session", long_error)

        assert len(ep.result_summary) <= 200

    def test_multiple_episodes_logged_sequentially(self, reset_session_service, temp_logs_dir):
        """Test logging multiple episodes to same file."""
        from services.episode_logger import log_user_message, log_stream_end

        ep1 = log_user_message("session-1")
        ep2 = log_stream_end(
            session_id="session-2",
            model="model",
            input_tokens=10,
            output_tokens=20,
            stream_start_ms=0,
            stream_end_ms=1000,
        )

        log_path = os.environ["EPISODE_LOG_PATH"]
        with open(log_path) as f:
            lines = f.readlines()
            assert len(lines) == 3  # header + 2 episodes

    def test_episode_persists_all_fields(self, reset_session_service, temp_logs_dir):
        """Test that all episode fields are persisted to CSV."""
        from services.episode_logger import log_stream_end
        import csv

        log_stream_end(
            session_id="test-session",
            model="test-model",
            input_tokens=100,
            output_tokens=200,
            stream_start_ms=1000,
            stream_end_ms=3000,
            was_cancelled=False,
        )

        log_path = os.environ["EPISODE_LOG_PATH"]
        with open(log_path) as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert row["session_id"] == "test-session"
            assert row["model"] == "test-model"
            assert row["input_tokens"] == "100"
            assert row["output_tokens"] == "200"
            assert row["latency_ms"] == "2000"

    def test_episode_cost_with_claude(self, reset_session_service, temp_logs_dir):
        """Test cost calculation for Claude models."""
        from services.episode_logger import log_stream_end

        ep = log_stream_end(
            session_id="session",
            model="anthropic/claude-sonnet-4-6",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            stream_start_ms=0,
            stream_end_ms=1000,
        )

        # Sonnet: input 3.00, output 15.00 per M
        expected_cost = 3.00 + 15.00
        assert ep.cost_usd == pytest.approx(expected_cost, rel=0.01)
