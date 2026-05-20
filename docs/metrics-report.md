# Metrics Report — Pocket Mechanics

**Generated:** 2026-05-20 20:16 UTC  
**Source log:** `C:\Users\romag\Documents\GitHub\Pocket_Mechanics\Backend\logs\episode-log.csv`  
**Total episode rows:** 19  
**LLM/stream events analysed:** 9

## Six key metrics (Week 11)

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Error rate | 0.0% | <= 5.0% | PASS |
| p95 latency | 4052 ms | <= 12000 ms | PASS |
| Median cost / call | $0.0 | <= $0.02 | PASS |
| Cache hit rate | 0.0% | informational | PASS |
| Fallback rate | 0.0% | <= 15.0% | PASS |
| Retry rate | 0.0% | <= 10.0% | PASS |

## Event mix

```json
{'user_message': 9, 'error': 1, 'stream_end': 9}
```

## Notes

- On Render, persist `EPISODE_LOG_PATH` to `/tmp/episode-log.csv` if you need cross-deploy history.
- Re-run after golden set or benchmark: `python scripts/metrics_report.py --write docs/metrics-report.md`
