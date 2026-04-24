"""
Pocket Mechanics MCP server — Lab 6.

Exposes one tool that calls the team FastAPI Lab 5 endpoint (real model, not mocked).

stdio transport: stdin is JSON-RPC only. Do not type shell commands into the same
terminal while this process runs — use MCP Inspector in a *second* terminal to spawn
this script, or pipe from a real MCP client.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Load repo root + Backend .env so POCKET_MECHANICS_API_URL can live next to API keys
_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")
load_dotenv(_root / "Backend" / ".env", override=False)

DEFAULT_API = "http://127.0.0.1:8000"


app = Server("pocket-mechanics-tools")


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
                "required": ["question"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name != "ask_pocket_mechanics_tip":
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": "unknown_tool", "tool": name}),
            )
        ]

    question = arguments.get("question")
    if not question or not isinstance(question, str) or not question.strip():
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": "invalid_argument", "message": "question must be a non-empty string"}),
            )
        ]

    vehicle = arguments.get("vehicle_hint") or ""
    if vehicle is not None and not isinstance(vehicle, str):
        vehicle = str(vehicle)
    vehicle = (vehicle or "").strip()[:200]

    prompt = question.strip()[:2000]
    if vehicle:
        prompt = f"Vehicle context: {vehicle}\n\nQuestion: {prompt}"

    base = os.environ.get("POCKET_MECHANICS_API_URL", DEFAULT_API).rstrip("/")
    url = f"{base}/api/ai/generate"

    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                url,
                json={"prompt": prompt},
                headers={"Content-Type": "application/json"},
            )
        latency_ms = int((time.perf_counter() - t0) * 1000)
        r.raise_for_status()
        data = r.json()
        payload = {
            "answer": data.get("content", ""),
            "model": data.get("model"),
            "input_tokens": data.get("input_tokens"),
            "output_tokens": data.get("output_tokens"),
            "latency_ms_api": data.get("latency_ms"),
            "latency_ms_mcp_client": latency_ms,
            "source": "pocket_mechanics_api",
        }
        return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]
    except httpx.HTTPStatusError as e:
        body = e.response.text[:500] if e.response is not None else ""
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "http_error",
                        "status": e.response.status_code if e.response else None,
                        "detail": str(e),
                        "body_preview": body,
                        "hint": "Start the Backend (uvicorn) and check POCKET_MECHANICS_API_URL / .env keys.",
                    },
                    indent=2,
                ),
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": "tool_failed", "message": str(e)}),
            )
        ]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
