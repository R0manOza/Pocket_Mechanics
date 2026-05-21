"""
Pocket Mechanics MCP server — Lab 6 baseline, Lab 8 production hardening.

- Bearer token auth (MCP_SECRET_KEY)
- Pydantic input validation
- Structured JSON audit logging (input hash, latency, status)
- Sanitised error responses (no tracebacks to callers)
"""

from __future__ import annotations

import asyncio
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
from pydantic import ValidationError

from audit_logger import audit_log
from auth import extract_bearer_token, verify_bearer_token
from episode_sync import log_mcp_episode
from validated_tool import PocketMechanicsTipInput, validate_tool_input


def _audit_and_episode(
    *,
    tool_name: str,
    input_dict: dict,
    result_status: str,
    latency_ms: int,
    error: str | None = None,
) -> None:
    audit_log(
        tool_name=tool_name,
        input_dict=input_dict,
        result_status=result_status,
        latency_ms=latency_ms,
        error=error,
    )
    log_mcp_episode(
        tool_name=tool_name,
        input_dict=input_dict,
        result_status=result_status,
        latency_ms=latency_ms,
        error=error,
    )

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")
load_dotenv(_root / "Backend" / ".env", override=False)

DEFAULT_API = "http://127.0.0.1:8000"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pocket-mechanics-mcp")

app = Server("pocket-mechanics-tools")


def _json_response(payload: dict) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(payload))]


def _error_response(code: str) -> list[types.TextContent]:
    return _json_response({"error": code})


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="ask_pocket_mechanics_tip",
            description=(
                "Ask Pocket Mechanics for beginner-friendly car maintenance help. "
                "Requires Bearer token in _auth_token (value of MCP_SECRET_KEY)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "_auth_token": {
                        "type": "string",
                        "description": "Bearer token matching MCP_SECRET_KEY",
                    },
                    "question": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 2000,
                    },
                    "vehicle_hint": {
                        "type": "string",
                        "maxLength": 200,
                    },
                },
                "required": ["_auth_token", "question"],
                "additionalProperties": False,
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    started = time.perf_counter()
    arguments = dict(arguments or {})

    def elapsed_ms() -> int:
        return max(1, int((time.perf_counter() - started) * 1000))

    token = extract_bearer_token(arguments)
    if not verify_bearer_token(token):
        _audit_and_episode(
            tool_name=name,
            input_dict=arguments,
            result_status="auth_failed",
            latency_ms=elapsed_ms(),
            error="unauthorized",
        )
        return _error_response("unauthorized")

    try:
        validated = validate_tool_input(name, arguments)
    except ValidationError:
        _audit_and_episode(
            tool_name=name,
            input_dict=arguments,
            result_status="validation_failed",
            latency_ms=elapsed_ms(),
            error="invalid_input",
        )
        return _error_response("invalid_input")
    except ValueError:
        _audit_and_episode(
            tool_name=name,
            input_dict=arguments,
            result_status="unknown_tool",
            latency_ms=elapsed_ms(),
            error="unknown_tool",
        )
        return _error_response("unknown_tool")

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
        _audit_and_episode(
            tool_name=name,
            input_dict=validated.model_dump(by_alias=True),
            result_status="ok",
            latency_ms=elapsed_ms(),
        )
        return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]
    except httpx.HTTPStatusError:
        _audit_and_episode(
            tool_name=name,
            input_dict=validated.model_dump(by_alias=True),
            result_status="error",
            latency_ms=elapsed_ms(),
            error="upstream_http_error",
        )
        return _json_response({"error": "upstream_http_error"})
    except Exception:
        logger.exception("MCP tool internal failure")
        _audit_and_episode(
            tool_name=name,
            input_dict=validated.model_dump(by_alias=True),
            result_status="error",
            latency_ms=elapsed_ms(),
            error="tool_execution_failed",
        )
        return _error_response("tool_execution_failed")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
