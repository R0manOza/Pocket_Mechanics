"""
Pocket Mechanics MCP server — Lab 6.

Exposes one tool that calls the team FastAPI Lab 5 endpoint (real model, not mocked).

stdio transport: stdin is JSON-RPC only. Do not type shell commands into the same
terminal while this process runs — use MCP Inspector in a *second* terminal to spawn
this script, or pipe from a real MCP client.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from pydantic import BaseModel, Field, ValidationError

# Load repo root + Backend .env so POCKET_MECHANICS_API_URL can live next to API keys
_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")
load_dotenv(_root / "Backend" / ".env", override=False)

DEFAULT_API = "http://127.0.0.1:8000"
MCP_SECRET = os.environ.get("MCP_SECRET_KEY", "")
MCP_LOG_PATH = Path(os.environ.get("MCP_LOG_PATH", _root / "logs" / "mcp-audit.jsonl"))

logger = logging.getLogger("pocket-mechanics-mcp")
logging.basicConfig(level=logging.INFO)

app = Server("pocket-mechanics-tools")


class PocketMechanicsTipInput(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    vehicle_hint: str = Field(default="", max_length=200)
    auth_token: str = Field(default="", alias="_auth_token")

    model_config = {"populate_by_name": True}


def _verify_token(token: str) -> bool:
    if not MCP_SECRET:
        logger.warning("MCP_SECRET_KEY is not configured; rejecting MCP tool call")
        return False
    return bool(token) and hmac.compare_digest(MCP_SECRET, token)


def _json_response(payload: dict) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(payload))]


def _error_response(code: str) -> list[types.TextContent]:
    return _json_response({"error": code})


def _audit_log(tool_name: str, input_dict: dict, result_status: str, latency_ms: int, error: str | None = None) -> None:
    redacted_input = {k: v for k, v in input_dict.items() if k != "_auth_token"}
    input_hash = hashlib.sha256(
        json.dumps(redacted_input, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]
    entry = {
        "ts": time.time(),
        "event_type": "mcp_tool_call",
        "tool_name": tool_name,
        "input_hash": input_hash,
        "result_status": result_status,
        "latency_ms": latency_ms,
        "error": error,
    }

    try:
        MCP_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MCP_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as exc:
        logger.warning("Unable to write MCP audit log: %s", type(exc).__name__)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="ask_pocket_mechanics_tip",
            description=(
                "Ask Pocket Mechanics for beginner-friendly car maintenance help: parts, fluids, "
                "warnings lights, or what to check before a trip. Call when the user intent is clearly "
                "about **their car** or general vehicle maintenance — not for unrelated topics. "
                "Examples: 'What does a check engine light mean?', 'How often should I change oil?', "
                "'What is a serpentine belt?'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "_auth_token": {
                        "type": "string",
                        "description": "Bearer token from MCP_SECRET_KEY",
                    },
                    "question": {
                        "type": "string",
                        "description": "The user's car or maintenance question in natural language",
                        "minLength": 1,
                        "maxLength": 2000,
                    },
                    "vehicle_hint": {
                        "type": "string",
                        "description": "Optional year/make/model or engine hint (e.g. '2014 Ford Focus 2.0L')",
                        "maxLength": 200,
                    },
                },
                "required": ["_auth_token", "question"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    started = time.perf_counter()
    arguments = dict(arguments or {})

    def elapsed_ms() -> int:
        return max(1, int((time.perf_counter() - started) * 1000))

    token = str(arguments.get("_auth_token", ""))
    if not _verify_token(token):
        _audit_log(name, arguments, "auth_failed", elapsed_ms())
        return _error_response("unauthorized")

    if name != "ask_pocket_mechanics_tip":
        _audit_log(name, arguments, "unknown_tool", elapsed_ms())
        return _error_response("unknown_tool")

    try:
        validated = PocketMechanicsTipInput(**arguments)
    except ValidationError as exc:
        _audit_log(name, arguments, "validation_failed", elapsed_ms(), f"{exc.error_count()} validation errors")
        return _error_response("invalid_input")

    vehicle = validated.vehicle_hint.strip()
    prompt = validated.question.strip()
    if vehicle:
        prompt = f"Vehicle context: {vehicle}\n\nQuestion: {prompt}"

    base = os.environ.get("POCKET_MECHANICS_API_URL", DEFAULT_API).rstrip("/")
    url = f"{base}/api/ai/generate"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                url,
                json={"prompt": prompt},
                headers={"Content-Type": "application/json"},
            )
        r.raise_for_status()
        data = r.json()
        payload = {
            "answer": data.get("content", ""),
            "model": data.get("model"),
            "input_tokens": data.get("input_tokens"),
            "output_tokens": data.get("output_tokens"),
            "latency_ms_api": data.get("latency_ms"),
            "latency_ms_mcp_client": elapsed_ms(),
            "source": "pocket_mechanics_api",
        }
        _audit_log(name, validated.model_dump(by_alias=True), "ok", elapsed_ms())
        return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else None
        _audit_log(name, validated.model_dump(by_alias=True), "error", elapsed_ms(), "HTTPStatusError")
        return _json_response({"error": "upstream_http_error", "status": status})
    except Exception as e:
        logger.error("MCP tool execution failed: %s", type(e).__name__, exc_info=True)
        _audit_log(name, validated.model_dump(by_alias=True), "error", elapsed_ms(), type(e).__name__)
        return _error_response("tool_execution_failed")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
