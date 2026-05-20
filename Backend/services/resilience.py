"""
Lab 7 — timeouts, bounded retries, and exponential backoff for external AI calls.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import TypeVar

from services import episode_logger

T = TypeVar("T")


def timeout_ms_from_env() -> int:
    seconds = os.environ.get(
        "LLM_TIMEOUT_SECONDS",
        os.environ.get("OPENROUTER_TIMEOUT_SECONDS", os.environ.get("GEMINI_TIMEOUT_SECONDS", "30")),
    )
    return int(float(seconds) * 1000)


def max_attempts_from_env() -> int:
    explicit = os.environ.get("LLM_MAX_ATTEMPTS")
    if explicit:
        return max(1, int(explicit))
    sdk_retries = int(os.environ.get("OPENROUTER_MAX_RETRIES", "2"))
    return sdk_retries + 1


def backoff_seconds(attempt_index: int) -> float:
    """Exponential backoff before retry attempt_index (0 = first retry wait)."""
    base = float(os.environ.get("LLM_BACKOFF_BASE_SECONDS", "0.5"))
    cap = float(os.environ.get("LLM_BACKOFF_CAP_SECONDS", "8"))
    return min(cap, base * (2**attempt_index))


def call_with_resilience(
    fn: Callable[[], T],
    *,
    session_id: str,
    model: str,
    timeout_ms: int | None = None,
    max_attempts: int | None = None,
) -> tuple[T, int]:
    """
    Invoke fn with bounded retries and exponential backoff between failures.
    Logs each failed attempt to the episode log (Lab 7 audit fields).
    Returns (result, retry_count).
    """
    timeout_ms = timeout_ms if timeout_ms is not None else timeout_ms_from_env()
    max_attempts = max_attempts if max_attempts is not None else max_attempts_from_env()
    last_error: Exception | None = None
    retries_used = 0

    for attempt in range(max_attempts):
        start = time.perf_counter()
        try:
            result = fn()
            latency_ms = max(1, int((time.perf_counter() - start) * 1000))
            return result, retries_used
        except Exception as exc:
            last_error = exc
            latency_ms = max(1, int((time.perf_counter() - start) * 1000))
            if attempt < max_attempts - 1:
                retries_used += 1
                episode_logger.log_llm_call(
                    session_id=session_id,
                    model=model,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    provider=episode_logger.extract_provider(model),
                    retry_count=retries_used,
                    timeout_ms=timeout_ms,
                    error=type(exc).__name__,
                )
                time.sleep(backoff_seconds(attempt))
            else:
                episode_logger.log_llm_call(
                    session_id=session_id,
                    model=model,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    provider=episode_logger.extract_provider(model),
                    retry_count=retries_used,
                    timeout_ms=timeout_ms,
                    error=type(exc).__name__,
                )

    raise RuntimeError(
        f"LLM call failed after {max_attempts} attempts: {type(last_error).__name__}"
    ) from last_error
