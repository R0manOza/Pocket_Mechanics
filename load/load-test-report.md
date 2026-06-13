# Load Test Report — Pocket Mechanics

Real run, 50 concurrent users for 2 minutes, against the local Docker backend
(`pocket-mechanics` image). Numbers below are from `load/results_stats.csv`.

## How this was run

```bash
locust -f load/locustfile.py \
  --host http://127.0.0.1:8000 \
  --users 50 --spawn-rate 5 --run-time 2m --headless \
  --csv load/results
```

- **Target:** `POST /api/ai/generate` (blocking LLM call) + `GET /health`
- **Concurrency:** 50 simulated users
- **Duration:** 2 minutes
- **Backend:** Docker image (`python:3.11-slim`), rate limiter active (30 req/min/IP)

## Results — `POST /api/ai/generate`

| Metric | Value |
|--------|-------|
| Requests | 955 |
| Failures | 0 (0.0%) |
| Throughput | 8.17 req/s |
| p50 latency | 6 ms |
| p95 latency | 850 ms |
| p99 latency | 4,200 ms |
| Max latency | 12,502 ms |

## Results — `GET /health`

| Metric | Value |
|--------|-------|
| Requests | 1,809 |
| Failures | 0 |
| p50 latency | 6 ms |
| p95 latency | 11 ms |
| p99 latency | 30 ms |
| Max latency | 285 ms |

## Aggregate

| Metric | Value |
|--------|-------|
| Total requests | 2,764 |
| Total failures | 0 (0.0%) |
| Throughput | 23.6 req/s |
| p50 / p95 / p99 | 6 / 13 / 1,300 ms |

## Observations

- **Zero failures across 2,764 requests.** Under sustained 50-user load the
  service never errored or timed out.
- **The rate limiter held as designed.** With a 30 req/min/IP cap, most
  `/api/ai/generate` requests beyond the budget received an instant structured
  `429` (counted as a handled response, not a failure — see `locustfile.py`).
  That is why the generate **median is only 6 ms**: throttled requests return
  immediately. The **p95/p99 (850 ms / 4.2 s)** reflect the requests that passed
  the limiter and actually hit the model — real LLM latency dominated by
  output-token generation.
- **`/health` stayed fast throughout** — p99 of **30 ms**, well under the 500 ms
  budget, even while the LLM endpoint was saturated. This confirms `/health` is
  decoupled from the model path (no LLM call), which is the hard-gate requirement.
- **Graceful degradation:** excess load is shed via `429 + retry_after_seconds`
  rather than crashing or queueing unboundedly.

## Notes on interpreting the numbers

- The low median on `/api/ai/generate` is an artifact of the rate limiter
  returning fast `429`s under load, not of the model being fast. Genuine model
  latency is the p95/p99 tail.
- This run was against the **local Docker backend**; a run against the deployed
  host would add network RTT and (on free tiers) a cold-start penalty on the
  first requests.
