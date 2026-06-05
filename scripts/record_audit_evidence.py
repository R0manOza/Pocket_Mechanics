"""
Append Week-11 audit evidence rows to episode log and MCP audit JSONL.

Run from repo root:
    python scripts/record_audit_evidence.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "Backend"
MCP_DIR = ROOT / "mcp-server"
LOGS = ROOT / "logs"
EPISODE_LOG = BACKEND / "logs" / "episode-log.jsonl"
MCP_AUDIT = LOGS / "mcp-audit.jsonl"
EVIDENCE = ROOT / "docs" / "evidence"

os.environ.setdefault("EPISODE_LOG_PATH", str(EPISODE_LOG))
os.environ.setdefault("MCP_LOG_PATH", str(MCP_AUDIT))
os.environ.setdefault("MCP_SECRET_KEY", "audit-evidence-secret")

sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(MCP_DIR))

from services.episode_logger import (  # noqa: E402
    log_error,
    log_llm_call,
    log_mcp_tool_call,
)


async def run_mcp_scenarios() -> list[dict]:
    import importlib

    import server as mcp_server

    importlib.reload(mcp_server)

    scenarios = [
        (
            "bad_token",
            {"_auth_token": "wrong-token", "question": "What is coolant?"},
        ),
        (
            "invalid_input",
            {"_auth_token": "audit-evidence-secret", "question": ""},
        ),
    ]
    outputs: list[dict] = []
    for label, args in scenarios:
        result = await mcp_server.call_tool("ask_pocket_mechanics_tip", args)
        text = result[0].text
        outputs.append({"scenario": label, "response": json.loads(text)})
    return outputs


def append_synthetic_rows() -> None:
    log_error(
        "audit_evidence",
        RuntimeError("synthetic_timeout_for_audit"),
        context="audit_evidence_script",
        retry_count=2,
        timeout_ms=30000,
    )
    log_llm_call(
        session_id="audit_evidence",
        model="google/this-model-does-not-exist",
        input_tokens=0,
        output_tokens=0,
        latency_ms=1200,
        fallback_triggered=True,
        error="ModelNotFound",
        retry_count=1,
        timeout_ms=30000,
    )
    log_mcp_tool_call(
        tool_name="ask_pocket_mechanics_tip",
        input_dict={"question": "audit sample", "vehicle_hint": ""},
        result_status="ok",
        latency_ms=42,
    )


def main() -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    append_synthetic_rows()
    mcp_outputs = asyncio.run(run_mcp_scenarios())

    out_file = EVIDENCE / "mcp-auth-terminal.txt"
    lines = ["# MCP auth / validation terminal evidence", ""]
    for item in mcp_outputs:
        lines.append(f"## {item['scenario']}")
        lines.append(json.dumps(item["response"], indent=2))
        lines.append("")
    out_file.write_text("\n".join(lines), encoding="utf-8")

    print(f"Episode log: {EPISODE_LOG}")
    print(f"MCP audit:   {MCP_AUDIT}")
    print(f"Terminal evidence: {out_file}")
    for item in mcp_outputs:
        print(f"\n[{item['scenario']}]")
        print(json.dumps(item["response"]))


if __name__ == "__main__":
    main()
