"""Lab 7 — resilience wrapper (timeout, backoff, episode logging)."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

backend_path = Path(__file__).resolve().parents[1] / "Backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


class TestResilience:
    def test_call_with_resilience_succeeds_first_try(self, temp_logs_dir):
        from services.resilience import call_with_resilience

        result, retries = call_with_resilience(
            lambda: "ok",
            session_id="s1",
            model="google/gemini-2.5-flash",
            max_attempts=3,
            timeout_ms=5000,
        )
        assert result == "ok"
        assert retries == 0

    def test_call_with_resilience_retries_then_succeeds(self, temp_logs_dir):
        from services.resilience import call_with_resilience

        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 2:
                raise TimeoutError("simulated")
            return "recovered"

        with patch("services.resilience.time.sleep"):
            result, retries = call_with_resilience(
                flaky,
                session_id="s2",
                model="google/gemini-2.5-flash",
                max_attempts=3,
                timeout_ms=1000,
            )

        assert result == "recovered"
        assert retries == 1

    def test_call_with_resilience_raises_after_max_attempts(self, temp_logs_dir):
        from services.resilience import call_with_resilience

        with patch("services.resilience.time.sleep"):
            with pytest.raises(RuntimeError, match="failed after"):
                call_with_resilience(
                    lambda: (_ for _ in ()).throw(ValueError("always")),
                    session_id="s3",
                    model="test-model",
                    max_attempts=2,
                    timeout_ms=500,
                )

        log_path = os.environ["EPISODE_LOG_PATH"]
        with open(log_path, encoding="utf-8") as f:
            body = f.read()
        assert "retry_count" in body.splitlines()[0]
        assert "llm_call" in body
