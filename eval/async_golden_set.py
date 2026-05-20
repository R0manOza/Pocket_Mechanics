#!/usr/bin/env python3
"""
Lab 9 — async golden set runner (httpx + optional LLM judge).

Loads eval/golden_set.json, calls POST /api/ai/generate concurrently, judges each answer.

  pip install httpx openai python-dotenv
  set OPENROUTER_KEY=...
  set POCKET_MECHANICS_API_URL=http://127.0.0.1:8000
  python eval/async_golden_set.py
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI

_REPO = Path(__file__).resolve().parents[1]
load_dotenv(_REPO / ".env")
load_dotenv(_REPO / "Backend" / ".env", override=True)

API_BASE = os.environ.get("POCKET_MECHANICS_API_URL", "http://127.0.0.1:8000").rstrip("/")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "google/gemini-2.5-flash")
CONCURRENCY = int(os.environ.get("GOLDEN_SET_CONCURRENCY", "3"))


def _parse_judge_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}\s*$", text)
    if not m:
        raise ValueError(f"No JSON in judge output: {text[:300]!r}")
    return json.loads(m.group(0))


async def fetch_answer(client: httpx.AsyncClient, prompt: str) -> str:
    r = await client.post(f"{API_BASE}/api/ai/generate", json={"prompt": prompt})
    r.raise_for_status()
    return str(r.json().get("content", "")).strip()


async def judge_one(
    judge: AsyncOpenAI,
    *,
    qid: str,
    question: str,
    criteria: str,
    answer: str,
) -> tuple[bool, str]:
    system = (
        'Strict judge. Reply ONLY JSON: {"pass": true|false, "reason": "short"}'
    )
    user = json.dumps(
        {
            "question_id": qid,
            "user_question": question,
            "grading_criteria": criteria,
            "agent_answer": answer[:8000],
        },
        ensure_ascii=False,
    )
    resp = await judge.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "").strip()
    data = _parse_judge_json(raw)
    return bool(data.get("pass")), str(data.get("reason", "")).strip()


async def run_item(
    http: httpx.AsyncClient,
    judge: AsyncOpenAI,
    item: dict,
    sem: asyncio.Semaphore,
) -> dict:
    async with sem:
        t0 = time.perf_counter()
        qid = item["id"]
        try:
            answer = await fetch_answer(http, item["prompt"])
            ok, reason = await judge_one(
                judge,
                qid=qid,
                question=item["prompt"],
                criteria=item["judge_criteria"],
                answer=answer,
            )
        except Exception as e:
            answer = ""
            ok = False
            reason = f"evaluation_error: {e}"
        dt_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "id": qid,
            "category": item["category"],
            "pass": ok,
            "reason": reason,
            "latency_ms": dt_ms,
            "agent_answer_excerpt": answer[:1200],
        }


async def main() -> int:
    key = os.environ.get("OPENROUTER_KEY", "").strip()
    if not key:
        raise SystemExit("OPENROUTER_KEY required for async judge")

    golden_path = _REPO / "eval" / "golden_set.json"
    items = json.loads(golden_path.read_text(encoding="utf-8"))["items"]
    if len(items) != 10:
        raise SystemExit(f"Expected 10 items, got {len(items)}")

    judge = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
    sem = asyncio.Semaphore(CONCURRENCY)
    out_dir = _REPO / "eval" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=120.0) as http:
        rows = await asyncio.gather(*[run_item(http, judge, it, sem) for it in items])

    passed = sum(1 for r in rows if r["pass"])
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    payload = {
        "run_id": f"golden-async-{run_ts}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_base_url": API_BASE,
        "concurrency": CONCURRENCY,
        "judge_model": JUDGE_MODEL,
        "overall_pass_count": passed,
        "overall_score_text": f"{passed}/10",
        "items": rows,
    }
    out_path = out_dir / f"golden-set-results-{run_ts}.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out_path), "pass_count": passed}, indent=2))
    return 0 if passed >= 7 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
