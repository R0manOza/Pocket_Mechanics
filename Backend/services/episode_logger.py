"""
Episode log — Lab 6 (streaming + events for Week 11 audit).
"""

import csv
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _default_log_path(filename: str) -> str:
    tmp = os.environ.get("TMPDIR") or os.environ.get("TEMP") or ""

    if os.path.isdir("/tmp"):
        return os.path.join("/tmp", filename)
    if tmp and os.path.isdir(tmp):
        return os.path.join(tmp, filename)

    return os.path.join("logs", filename)


def _log_file() -> str:
    return os.environ.get("EPISODE_LOG_PATH", _default_log_path("episode-log.csv"))


MODEL_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-flash-lite": {"input": 0.00, "output": 0.00},
    "gemini-2.5-flash": {"input": 0.00, "output": 0.00},
    "gemini-2.5-pro": {"input": 0.00, "output": 0.00},
    "meta-llama/llama-4-maverick:free": {"input": 0.00, "output": 0.00},
    "google/gemma-3-27b-it:free": {"input": 0.00, "output": 0.00},
    "deepseek/deepseek-r1:free": {"input": 0.00, "output": 0.00},
    "openrouter/free": {"input": 0.00, "output": 0.00},
    "google/gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "google/gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "anthropic/claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "anthropic/claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
}


@dataclass
class Episode:
    session_id: str
    event_type: str
    episode_id: str = field(default_factory=lambda: f"ep_{uuid.uuid4().hex[:12]}")
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model: str | None = None
    tool_name: str | None = None
    arguments: str | None = None
    result_summary: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    stream_start_ms: int | None = None
    stream_end_ms: int | None = None
    latency_ms: int = 0
    was_cancelled: bool = False
    success: bool = True
    cost_usd: float = 0.0


def log_episode(ep: Episode) -> Episode:
    ep.cost_usd = _calculate_cost(ep.model or "", ep.input_tokens, ep.output_tokens)
    row = asdict(ep)

    label = ep.tool_name or ep.model or "-"
    print(
        f"[EPISODE] {ep.ts[:19]} | {ep.event_type:<15} | {label:<30} | "
        f"in={ep.input_tokens} out={ep.output_tokens} | {ep.latency_ms}ms | ${ep.cost_usd:.6f}"
    )

    try:
        log_file = _log_file()
        log_dir = os.path.dirname(log_file)

        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_exists = os.path.isfile(log_file)

        with open(log_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    except OSError:
        # Read-only filesystem, e.g. Vercel, or other IO failure.
        # Keep stdout logging so the request still succeeds.
        pass

    return ep


def log_user_message(session_id: str) -> Episode:
    return log_episode(Episode(session_id=session_id, event_type="user_message"))


def log_stream_end(
    session_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    stream_start_ms: int,
    stream_end_ms: int,
    was_cancelled: bool = False,
) -> Episode:
    return log_episode(
        Episode(
            session_id=session_id,
            event_type="stream_end",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            stream_start_ms=stream_start_ms,
            stream_end_ms=stream_end_ms,
            latency_ms=stream_end_ms - stream_start_ms,
            was_cancelled=was_cancelled,
        )
    )


def log_tool_call(
    session_id: str,
    tool_name: str,
    arguments: dict,
    result: Any,
    latency_ms: int,
    success: bool = True,
) -> Episode:
    result_str = str(result) if result is not None else ""

    return log_episode(
        Episode(
            session_id=session_id,
            event_type="tool_call",
            tool_name=tool_name,
            arguments=json.dumps(arguments),
            result_summary=result_str[:200] if result_str else None,
            latency_ms=latency_ms,
            success=success,
        )
    )


def log_error(session_id: str, error: Exception, context: str = "") -> Episode:
    msg = f"{context}: {str(error)[:190]}" if context else str(error)[:200]

    return log_episode(
        Episode(
            session_id=session_id,
            event_type="error",
            result_summary=msg,
            success=False,
        )
    )


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens / 1_000_000) * pricing["input"] + (
        output_tokens / 1_000_000
    ) * pricing["output"]