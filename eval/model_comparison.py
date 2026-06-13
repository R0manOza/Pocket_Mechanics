#!/usr/bin/env python3
"""
Model comparison benchmark — Lab 11 portability evidence.

Benchmarks 3+ models across 5+ questions through the running Pocket Mechanics
backend (`POST /api/ai/generate`) and writes `eval/model-comparison.json` with
per-model latency, cost, and token numbers.

Run once with a running backend + OPENROUTER_KEY set (real data, not faked):

    # local
    uv run uvicorn main:app --port 8000        # in Backend/, separate terminal
    python eval/model_comparison.py --base-url http://127.0.0.1:8000

    # or against the deployed API
    python eval/model_comparison.py --base-url https://<your-backend>

Override the model set:

    python eval/model_comparison.py --models google/gemini-2.5-flash,openai/gpt-5.5,deepseek/deepseek-v4-flash
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import httpx

_REPO_ROOT = Path(__file__).resolve().parents[1]

# 5 questions spanning factual + reasoning, short enough to bound output tokens.
QUESTIONS = [
    "In one sentence, what is a serpentine belt?",
    "What does a flashing check engine light mean?",
    "Can I drive with low coolant? One sentence.",
    "What is brake fluid for? One sentence.",
    "What does the W in a 5W-30 oil grade mean?",
]

# 3 models from different vendors (portability — proves the provider abstraction
# works across vendors, not just one). All read at runtime; nothing hardcoded in app source.
DEFAULT_MODELS = [
    "google/gemini-2.5-flash",
    "openai/gpt-5.5",
    "deepseek/deepseek-v4-flash",
]


def benchmark_model(client: httpx.Client, base_url: str, model: str) -> dict:
    url = f"{base_url.rstrip('/')}/api/ai/generate"
    per_question = []
    for q in QUESTIONS:
        resp = client.post(url, json={"prompt": q, "model": model})
        resp.raise_for_status()
        d = resp.json()
        per_question.append(
            {
                "question": q,
                "latency_ms": int(d.get("latency_ms", 0)),
                "input_tokens": int(d.get("input_tokens", 0)),
                "output_tokens": int(d.get("output_tokens", 0)),
                "cost_usd": float(d.get("cost_usd", 0.0)),
                "model_used": d.get("model_used") or d.get("model", model),
                "answer_excerpt": (d.get("content", "") or "")[:200],
            }
        )
    latencies = [r["latency_ms"] for r in per_question]
    costs = [r["cost_usd"] for r in per_question]
    return {
        "model": model,
        "questions_run": len(per_question),
        "avg_latency_ms": round(statistics.mean(latencies), 1) if latencies else 0,
        "median_latency_ms": statistics.median(latencies) if latencies else 0,
        "avg_cost_usd": round(statistics.mean(costs), 8) if costs else 0.0,
        "total_cost_usd": round(sum(costs), 8),
        "per_question": per_question,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="Comma-separated model slugs (>=3 recommended).",
    )
    ap.add_argument("--out", type=Path, default=_REPO_ROOT / "eval" / "model-comparison.json")
    args = ap.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    results = []
    with httpx.Client(timeout=180.0) as client:
        for model in models:
            print(f"Benchmarking {model} ...")
            try:
                results.append(benchmark_model(client, args.base_url, model))
            except Exception as e:  # noqa: BLE001 — record the failure, keep going
                print(f"  failed: {e}")
                results.append({"model": model, "error": str(e), "questions_run": 0})

    out = {
        "description": "Lab 11 model comparison — latency/cost/tokens across vendors via the Pocket Mechanics API.",
        "questions": QUESTIONS,
        "models_compared": len(results),
        "results": results,
    }
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {args.out}  ({len(results)} models x {len(QUESTIONS)} questions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
