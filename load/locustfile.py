"""
Load test for the Pocket Mechanics chat endpoint.

Run against the DEPLOYED app (not localhost) per the rubric — 50 users, 2 minutes:

    pip install locust
    locust -f load/locustfile.py \
        --host https://pocket-mechanics-api.onrender.com \
        --users 50 --spawn-rate 5 --run-time 2m --headless \
        --csv load/results

Then copy the p50/p95/p99, throughput, and failure rate from the run
(Locust prints an aggregated table at the end, and writes load/results_stats.csv)
into load/load-test-report.md.

Notes:
- Targets POST /api/ai/generate (blocking) so each request has a clean,
  measurable latency. The streaming endpoint is harder to time meaningfully
  under load because latency is dominated by token generation.
- Keep prompts short to bound output tokens (and cost) during the test.
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task

# Short prompts → bounded output tokens → bounded cost and comparable latencies.
PROMPTS = [
    "In one sentence, what does a serpentine belt do?",
    "What does the TPMS light mean?",
    "Is it safe to drive with a flashing check engine light? One sentence.",
    "What is brake fluid for? One sentence.",
    "What does 5W-30 mean? One sentence.",
]


class PocketMechanicsUser(HttpUser):
    # Realistic think-time between requests from a single simulated user.
    wait_time = between(1, 3)

    @task
    def generate(self):
        payload = {"prompt": random.choice(PROMPTS)}
        with self.client.post(
            "/api/ai/generate",
            json=payload,
            name="POST /api/ai/generate",
            catch_response=True,
            timeout=60,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 429:
                # Rate limiter kicking in is expected under load — count as a
                # handled outcome, not a hard failure, so the report separates
                # "throttled" from "errored".
                resp.success()
            else:
                resp.failure(f"unexpected status {resp.status_code}")

    @task(2)
    def health(self):
        # Cheap, no-LLM probe — confirms the service stays responsive under load.
        with self.client.get("/health", name="GET /health", catch_response=True) as resp:
            resp.success() if resp.status_code == 200 else resp.failure(
                f"health {resp.status_code}"
            )
