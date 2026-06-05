"""
Episode log — Lab 6 streaming + Lab 7 resilience fields (Week 11 audit).

Writes JSONL (one JSON object per line) by default — see logs/episode-log.jsonl.
Set EPISODE_LOG_PATH to a .csv path only if you need legacy CSV output.
"""

import csv
import hashlib
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
    return os.environ.get("EPISODE_LOG_PATH", _default_log_path("episode-log.jsonl"))


def _use_csv_format(log_file: str) -> bool:
    return log_file.lower().endswith(".csv")


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
    "openai/gpt-5-nano": {"input": 0.05, "output": 0.40}
}


@dataclass
class Episode:
    session_id: str
    event_type: str
    episode_id: str = field(default_factory=lambda: f"ep_{uuid.uuid4().hex[:12]}")
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model: str | None = None
    tool_name: str | None = None
    provider: str | None = None
    input_hash: str | None = None
    result_status: str | None = None
    arguments: str | None = None
    result_summary: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    stream_start_ms: int | None = None
    stream_end_ms: int | None = None
    latency_ms: int = 0
    fallback_triggered: bool = False
    was_cancelled: bool = False
    success: bool = True
    cost_usd: float = 0.0
    error: str | None = None
    retry_count: int = 0
    timeout_ms: int | None = None


def _ts_unix(ep: Episode) -> float:
    if ep.ts:
        return datetime.fromisoformat(ep.ts.replace("Z", "+00:00")).timestamp()
    return datetime.now(timezone.utc).timestamp()


def _entry_for_jsonl(ep: Episode) -> dict[str, Any]:
    """
    Course audit shape: required fields only per event_type (Lab 8 / Week 11).
    Extra internal fields (session_id, retry_count, …) go under \"meta\" so graders
  see the canonical keys first — not empty CSV-style columns on every row.
    """
    ts = _ts_unix(ep)
    meta: dict[str, Any] = {
        "session_id": ep.session_id,
        "episode_id": ep.episode_id,
    }
    if ep.retry_count:
        meta["retry_count"] = ep.retry_count
    if ep.timeout_ms is not None:
        meta["timeout_ms"] = ep.timeout_ms
    if ep.was_cancelled:
        meta["was_cancelled"] = True
    if not ep.success:
        meta["success"] = False
    if ep.result_summary:
        meta["result_summary"] = ep.result_summary
    if ep.arguments:
        meta["arguments"] = ep.arguments

    if ep.event_type == "llm_call":
        entry: dict[str, Any] = {
            "ts": ts,
            "event_type": "llm_call",
            "model": ep.model or "unknown",
            "input_tokens": ep.input_tokens,
            "output_tokens": ep.output_tokens,
            "cache_read_tokens": ep.cache_read_tokens,
            "cache_write_tokens": ep.cache_write_tokens,
            "cost_usd": ep.cost_usd,
            "latency_ms": ep.latency_ms,
            "provider": ep.provider or extract_provider(ep.model or ""),
            "fallback_triggered": ep.fallback_triggered,
            "error": ep.error,
        }
    elif ep.event_type == "mcp_tool_call":
        entry = {
            "ts": ts,
            "event_type": "mcp_tool_call",
            "tool_name": ep.tool_name or "unknown",
            "input_hash": ep.input_hash or "",
            "result_status": ep.result_status or "unknown",
            "latency_ms": ep.latency_ms,
            "error": ep.error,
        }
    elif ep.event_type == "stream_end":
        entry = {
            "ts": ts,
            "event_type": "stream_end",
            "model": ep.model or "unknown",
            "input_tokens": ep.input_tokens,
            "output_tokens": ep.output_tokens,
            "cache_read_tokens": ep.cache_read_tokens,
            "cache_write_tokens": ep.cache_write_tokens,
            "cost_usd": ep.cost_usd,
            "latency_ms": ep.latency_ms,
            "provider": ep.provider or extract_provider(ep.model or ""),
            "fallback_triggered": ep.fallback_triggered,
            "error": ep.error,
        }
        if ep.stream_start_ms is not None:
            meta["stream_start_ms"] = ep.stream_start_ms
        if ep.stream_end_ms is not None:
            meta["stream_end_ms"] = ep.stream_end_ms
    elif ep.event_type == "error":
        entry = {
            "ts": ts,
            "event_type": "error",
            "error": ep.error or "Error",
            "latency_ms": ep.latency_ms,
        }
    else:
        entry = {
            "ts": ts,
            "event_type": ep.event_type,
            "error": ep.error,
        }

    entry["meta"] = meta
    return entry


def log_episode(ep: Episode) -> Episode:
    ep.cost_usd = _calculate_cost(ep.model or "", ep.input_tokens, ep.output_tokens)
    row = asdict(ep)

    label = ep.tool_name or ep.model or "-"
    retry_note = f" retries={ep.retry_count}" if ep.retry_count else ""
    err_note = f" err={ep.error}" if ep.error else ""
    print(
        f"[EPISODE] {ep.ts[:19]} | {ep.event_type:<15} | {label:<30} | "
        f"in={ep.input_tokens} out={ep.output_tokens} | {ep.latency_ms}ms{retry_note}{err_note} | "
        f"${ep.cost_usd:.6f}"
    )

    try:
        log_file = _log_file()
        log_dir = os.path.dirname(log_file)

        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        if _use_csv_format(log_file):
            file_exists = os.path.isfile(log_file)
            with open(log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
        else:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(_entry_for_jsonl(ep), default=str) + "\n")

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
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    fallback_triggered: bool = False,
    retry_count: int = 0,
    timeout_ms: int | None = None,
    error: str | None = None,
) -> Episode:
    return log_episode(
        Episode(
            session_id=session_id,
            event_type="stream_end",
            model=model,
            provider=extract_provider(model),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            stream_start_ms=stream_start_ms,
            stream_end_ms=stream_end_ms,
            latency_ms=stream_end_ms - stream_start_ms,
            fallback_triggered=fallback_triggered,
            was_cancelled=was_cancelled,
            retry_count=retry_count,
            timeout_ms=timeout_ms,
            success=error is None,
            error=error,
        )
    )


def log_llm_call(
    session_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    cost_usd: float = 0.0,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    provider: str | None = None,
    fallback_triggered: bool = False,
    error: str | None = None,
    retry_count: int = 0,
    timeout_ms: int | None = None,
) -> Episode:
    return log_episode(
        Episode(
            session_id=session_id,
            event_type="llm_call",
            model=model,
            provider=provider or extract_provider(model),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            fallback_triggered=fallback_triggered,
            success=error is None,
            error=error,
            retry_count=retry_count,
            timeout_ms=timeout_ms,
        )
    )


def log_mcp_tool_call(
    tool_name: str,
    input_dict: dict,
    result_status: str,
    latency_ms: int,
    error: str | None = None,
    session_id: str = "mcp",
) -> Episode:
    input_hash = hashlib.sha256(
        json.dumps(input_dict, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]

    return log_episode(
        Episode(
            session_id=session_id,
            event_type="mcp_tool_call",
            tool_name=tool_name,
            input_hash=input_hash,
            result_status=result_status,
            latency_ms=latency_ms,
            success=result_status == "ok",
            error=error,
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


def log_error(
    session_id: str,
    error: Exception,
    context: str = "",
    *,
    retry_count: int = 0,
    timeout_ms: int | None = None,
) -> Episode:
    msg = f"{context}: {str(error)[:190]}" if context else str(error)[:200]

    return log_episode(
        Episode(
            session_id=session_id,
            event_type="error",
            result_summary=msg,
            success=False,
            error=type(error).__name__,
            retry_count=retry_count,
            timeout_ms=timeout_ms,
        )
    )


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens / 1_000_000) * pricing["input"] + (
        output_tokens / 1_000_000
    ) * pricing["output"]


def extract_provider(model_string: str) -> str:
    if "/" in model_string:
        return model_string.split("/", 1)[0]
    if "claude" in model_string:
        return "anthropic"
    if "gemini" in model_string:
        return "google"
    if "gpt" in model_string:
        return "openai"
    return "unknown"
