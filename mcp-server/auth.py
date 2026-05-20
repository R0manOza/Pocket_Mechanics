"""Lab 8 — Bearer token verification (env-only secret, constant-time compare)."""

from __future__ import annotations

import hmac
import logging
import os

logger = logging.getLogger("pocket-mechanics-mcp.auth")

MCP_SECRET = os.environ.get("MCP_SECRET_KEY", "").strip()


def extract_bearer_token(arguments: dict) -> str:
    """Accept MCP tool arg `_auth_token` or `authorization: Bearer <token>`."""
    if not arguments:
        return ""
    direct = str(arguments.get("_auth_token", "")).strip()
    if direct:
        return direct
    auth = str(arguments.get("authorization", "")).strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return auth


def verify_bearer_token(token: str) -> bool:
    if not MCP_SECRET:
        logger.warning("MCP_SECRET_KEY is not configured; rejecting MCP tool call")
        return False
    if not token:
        return False
    return hmac.compare_digest(MCP_SECRET, token)
