"""Lab 8 — structured JSON audit log (input hash only, never raw secrets)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger("pocket-mechanics-mcp.audit")

_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_PATH = Path(os.environ.get("MCP_LOG_PATH", _ROOT / "logs" / "mcp-audit.jsonl"))


def input_hash(redacted: dict) -> str:
    payload = json.dumps(redacted, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def audit_log(
    *,
    tool_name: str,
    input_dict: dict,
    result_status: str,
    latency_ms: int,
    error: str | None = None,
    log_path: Path | None = None,
) -> None:
    redacted = {k: v for k, v in input_dict.items() if k not in ("_auth_token", "authorization")}
    entry = {
        "ts": time.time(),
        "event_type": "mcp_tool_call",
        "tool_name": tool_name,
        "input_hash": input_hash(redacted),
        "result_status": result_status,
        "latency_ms": latency_ms,
        "error": error,
    }
    logger.info("mcp_audit %s", json.dumps(entry, default=str))

    path = log_path or DEFAULT_LOG_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as exc:
        logger.warning("Unable to write MCP audit log: %s", type(exc).__name__)
