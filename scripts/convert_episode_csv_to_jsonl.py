#!/usr/bin/env python3
"""
Convert episode-log.csv → episode-log.jsonl (course audit field shapes).

Usage:
  python scripts/convert_episode_csv_to_jsonl.py
  python scripts/convert_episode_csv_to_jsonl.py --input Backend/logs/episode-log.csv --output Backend/logs/episode-log.jsonl
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_BACKEND = _REPO / "Backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from services.episode_logger import Episode, _entry_for_jsonl  # noqa: E402

_BOOL_FIELDS = {"fallback_triggered", "was_cancelled", "success"}
_INT_FIELDS = {
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "stream_start_ms",
    "stream_end_ms",
    "latency_ms",
    "retry_count",
    "timeout_ms",
}
_FLOAT_FIELDS = {"cost_usd"}


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def csv_row_to_episode(row: dict) -> Episode:
    kwargs: dict = {}
    for key, raw in row.items():
        if raw is None or str(raw).strip() == "":
            continue
        if key in _BOOL_FIELDS:
            kwargs[key] = _parse_bool(raw)
        elif key in _INT_FIELDS:
            kwargs[key] = int(float(raw))
        elif key in _FLOAT_FIELDS:
            kwargs[key] = float(raw)
        else:
            kwargs[key] = str(raw).strip()
    return Episode(**kwargs)


def convert(input_path: Path, output_path: Path) -> int:
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with open(input_path, newline="", encoding="utf-8") as src, open(
        output_path, "w", encoding="utf-8"
    ) as dst:
        for row in csv.DictReader(src):
            ep = csv_row_to_episode(row)
            dst.write(json.dumps(_entry_for_jsonl(ep), default=str) + "\n")
            count += 1

    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert episode CSV to audit JSONL")
    parser.add_argument(
        "--input",
        type=Path,
        default=_REPO / "Backend" / "logs" / "episode-log.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_REPO / "Backend" / "logs" / "episode-log.jsonl",
    )
    args = parser.parse_args()
    n = convert(args.input, args.output)
    print(f"Wrote {n} entries to {args.output}")


if __name__ == "__main__":
    main()
