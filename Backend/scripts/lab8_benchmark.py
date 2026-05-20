"""
Run the Lab 8 10-call benchmark against the local or deployed API.

Examples:
    python Backend/scripts/lab8_benchmark.py --base-url http://127.0.0.1:8000
    python Backend/scripts/lab8_benchmark.py --base-url https://your-api.vercel.app
"""

from __future__ import annotations

import argparse
import statistics
from dataclasses import dataclass

import httpx


QUESTIONS = [
    "What is a serpentine belt?",
    "How often should I check engine oil?",
    "What does a flashing check engine light mean?",
    "Can I drive with low coolant?",
    "What is brake fluid for?",
] * 2


@dataclass
class Result:
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_usd: float
    latency_ms: int


def run_benchmark(base_url: str, model: str | None = None) -> list[Result]:
    results: list[Result] = []
    url = f"{base_url.rstrip('/')}/api/ai/generate"

    with httpx.Client(timeout=120.0) as client:
        for question in QUESTIONS:
            body: dict[str, str] = {"prompt": question}
            if model:
                body["model"] = model
            response = client.post(url, json=body)
            response.raise_for_status()
            data = response.json()
            results.append(
                Result(
                    input_tokens=int(data.get("input_tokens", 0)),
                    output_tokens=int(data.get("output_tokens", 0)),
                    cache_read_tokens=int(data.get("cache_read_tokens", 0)),
                    cache_write_tokens=int(data.get("cache_write_tokens", 0)),
                    cost_usd=float(data.get("cost_usd", 0)),
                    latency_ms=int(data.get("latency_ms", 0)),
                )
            )

    return results


def print_markdown(results: list[Result]) -> None:
    print("| Call # | Input Tokens | Cache Read Tokens | Cache Write Tokens | Cost (USD) | Latency (ms) |")
    print("|--------|-------------|------------------|-------------------|------------|--------------|")
    for index, result in enumerate(results, start=1):
        print(
            f"| {index} | {result.input_tokens} | {result.cache_read_tokens} | "
            f"{result.cache_write_tokens} | {result.cost_usd:.8f} | {result.latency_ms} |"
        )
    print()
    print(f"Median latency (ms): {statistics.median(r.latency_ms for r in results)}")
    print(f"Total cost (USD): {sum(r.cost_usd for r in results):.8f}")
    print(f"Average cost per call (USD): {statistics.mean(r.cost_usd for r in results):.8f}")
    print(f"Cache hit rate: {sum(1 for r in results if r.cache_read_tokens > 0)}/{len(results)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()
    print_markdown(run_benchmark(args.base_url, args.model))


if __name__ == "__main__":
    main()
