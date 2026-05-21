"""Mirror MCP audit events into the backend episode CSV when Backend is on PYTHONPATH."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger("pocket-mechanics-mcp.episode_sync")

_BACKEND = Path(__file__).resolve().parent.parent / "Backend"


def log_mcp_episode(
    *,
    tool_name: str,
    input_dict: dict,
    result_status: str,
    latency_ms: int,
    error: str | None = None,
) -> None:
    try:
        backend_path = str(_BACKEND)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        from services.episode_logger import log_mcp_tool_call

        log_mcp_tool_call(
            tool_name=tool_name,
            input_dict=input_dict,
            result_status=result_status,
            latency_ms=latency_ms,
            error=error,
        )
    except Exception as exc:
        logger.debug("Episode CSV sync skipped: %s", type(exc).__name__)
