#!/usr/bin/env python3
"""
Lab 9 — compute six observability metrics from episode log (JSONL or CSV).

Usage:
  python scripts/metrics_report.py
  python scripts/metrics_report.py --log Backend/logs/episode-log.jsonl --write docs/metrics-report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

THRESHOLDS = {
    "error_rate_pct_max": 5.0,
    "p95_latency_ms_max": 12_000,
    "median_cost_usd_max": 0.02,
    "cache_hit_rate_pct_min": 0.0,  # 0% OK when not using Anthropic cache
    "fallback_rate_pct_max": 15.0,
    "retry_rate_pct_max": 10.0,
}


def _resolve_log(path: str | None) -> Path:
    if path:
        return Path(path)
    env = os.environ.get("EPISODE_LOG_PATH")
    if env:
        return Path(env)
    jsonl = _REPO / "Backend" / "logs" / "episode-log.jsonl"
    if jsonl.is_file():
        return jsonl
    return _REPO / "Backend" / "logs" / "episode-log.csv"


def load_rows(log_path: Path) -> list[dict]:
    if not log_path.is_file():
        return []
    if log_path.suffix.lower() == ".jsonl":
        rows: list[dict] = []
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    with open(log_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_metrics(rows: list[dict]) -> dict:
    llm_rows = [r for r in rows if r.get("event_type") in ("llm_call", "stream_end")]
    if not llm_rows:
        return {"row_count": len(rows), "llm_events": 0}

    latencies = [int(r.get("latency_ms") or 0) for r in llm_rows]
    costs = [float(r.get("cost_usd") or 0) for r in llm_rows]
    def _as_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1")

    successes = [_as_bool(r.get("success", True)) for r in llm_rows]
    fallbacks = [_as_bool(r.get("fallback_triggered", False)) for r in llm_rows]
    retries = [int(r.get("retry_count") or 0) > 0 for r in llm_rows]
    cache_hits = [int(r.get("cache_read_tokens") or 0) > 0 for r in llm_rows]

    error_rate = 100.0 * (1 - sum(successes) / len(successes))
    p95 = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)]
    median_cost = statistics.median(costs) if costs else 0.0
    cache_hit_rate = 100.0 * sum(cache_hits) / len(cache_hits)
    fallback_rate = 100.0 * sum(fallbacks) / len(fallbacks)
    retry_rate = 100.0 * sum(retries) / len(retries)

    return {
        "row_count": len(rows),
        "llm_events": len(llm_rows),
        "error_rate_pct": round(error_rate, 2),
        "p95_latency_ms": p95,
        "median_cost_usd": round(median_cost, 6),
        "cache_hit_rate_pct": round(cache_hit_rate, 2),
        "fallback_rate_pct": round(fallback_rate, 2),
        "retry_rate_pct": round(retry_rate, 2),
        "event_types": dict(Counter(r.get("event_type") for r in rows)),
    }


def pass_fail(metrics: dict) -> dict[str, str]:
    if metrics.get("llm_events", 0) == 0:
        return {k: "NO_DATA" for k in THRESHOLDS}
    return {
        "error_rate": "PASS" if metrics["error_rate_pct"] <= THRESHOLDS["error_rate_pct_max"] else "FAIL",
        "p95_latency": "PASS" if metrics["p95_latency_ms"] <= THRESHOLDS["p95_latency_ms_max"] else "FAIL",
        "median_cost": "PASS" if metrics["median_cost_usd"] <= THRESHOLDS["median_cost_usd_max"] else "FAIL",
        "cache_hit_rate": "PASS",  # informational unless Anthropic primary
        "fallback_rate": "PASS" if metrics["fallback_rate_pct"] <= THRESHOLDS["fallback_rate_pct_max"] else "FAIL",
        "retry_rate": "PASS" if metrics["retry_rate_pct"] <= THRESHOLDS["retry_rate_pct_max"] else "FAIL",
    }


def render_markdown(metrics: dict, verdicts: dict[str, str], log_path: Path) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""# Metrics Report — Pocket Mechanics

**Generated:** {ts}  
**Source log:** `{log_path}`  
**Total episode rows:** {metrics.get("row_count", 0)}  
**LLM/stream events analysed:** {metrics.get("llm_events", 0)}

## Six key metrics (Week 11)

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Error rate | {metrics.get("error_rate_pct", "n/a")}% | <= {THRESHOLDS["error_rate_pct_max"]}% | {verdicts.get("error_rate", "NO_DATA")} |
| p95 latency | {metrics.get("p95_latency_ms", "n/a")} ms | <= {THRESHOLDS["p95_latency_ms_max"]} ms | {verdicts.get("p95_latency", "NO_DATA")} |
| Median cost / call | ${metrics.get("median_cost_usd", "n/a")} | <= ${THRESHOLDS["median_cost_usd_max"]} | {verdicts.get("median_cost", "NO_DATA")} |
| Cache hit rate | {metrics.get("cache_hit_rate_pct", "n/a")}% | informational | {verdicts.get("cache_hit_rate", "NO_DATA")} |
| Fallback rate | {metrics.get("fallback_rate_pct", "n/a")}% | <= {THRESHOLDS["fallback_rate_pct_max"]}% | {verdicts.get("fallback_rate", "NO_DATA")} |
| Retry rate | {metrics.get("retry_rate_pct", "n/a")}% | <= {THRESHOLDS["retry_rate_pct_max"]}% | {verdicts.get("retry_rate", "NO_DATA")} |

## Event mix

```json
{metrics.get("event_types", {})}
```

## Notes

- On Render, persist `EPISODE_LOG_PATH` to `/tmp/episode-log.csv` if you need cross-deploy history.
- Re-run after golden set or benchmark: `python scripts/metrics_report.py --write docs/metrics-report.md`
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=None)
    ap.add_argument("--write", type=Path, default=None, help="Write markdown report to this path")
    args = ap.parse_args()

    log_path = _resolve_log(args.log)
    rows = load_rows(log_path)
    metrics = compute_metrics(rows)
    verdicts = pass_fail(metrics)

    print(render_markdown(metrics, verdicts, log_path))
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(render_markdown(metrics, verdicts, log_path), encoding="utf-8")
        print(f"\nWrote {args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
