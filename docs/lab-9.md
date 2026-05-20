# Lab 9 — Golden set + hardening (Pocket Mechanics)

## Part 1 — Golden set + safety audit doc

| Deliverable | Status |
|-------------|--------|
| `eval/golden_set.json` (10 questions) | Done |
| `eval/run_golden_set.py` | Done |
| `eval/async_golden_set.py` | Done |
| `docs/safety-audit.md` | Done — complete all six areas before **21 May 23:59** |
| Results in `eval/results/` | e.g. `golden-set-results-20260520-192243.json` (9/10) |

```bash
python eval/run_golden_set.py
# faster parallel:
python eval/async_golden_set.py
```

## Part 2 — Hardening

| Deliverable | Command |
|-------------|---------|
| `docs/metrics-report.md` | `python scripts/metrics_report.py --write docs/metrics-report.md` |
| Model selection table | Root `README.md` |

## Tag

```bash
git tag lab9-hardening
git push origin main --tags
```

## Render / Vercel

- **Render:** redeploy after push; golden set hits `POCKET_MECHANICS_API_URL` (your Render URL).
- **Vercel:** no change required for eval harness; frontend unchanged.
