# Golden test set & evaluation (Area 5)

## Files

| File | Purpose |
|------|---------|
| `golden_set.json` | 10 questions with `judge_criteria` rubrics (factual, reasoning, refusal, edge, format). |
| `run_golden_set.py` | Calls `POST /api/ai/generate`, then **LLM-as-judge** via OpenRouter (default `JUDGE_MODEL=google/gemini-2.5-flash`). |
| `results/golden-set-results-*.json` | Output from each run (committed: latest smoke run). |

## Full evaluation (LLM judge — required for audit evidence)

From repo root, with backend running and keys set:

```bash
# Windows PowerShell
$env:POCKET_MECHANICS_API_URL="http://127.0.0.1:8000"
$env:OPENROUTER_KEY="..."   # same OpenRouter key pattern as Backend
python eval/run_golden_set.py
```

This writes `eval/results/golden-set-results-<UTC-timestamp>.json`. Commit that file and update `docs/safety-audit.md` Area 5 table + “most recent results” link.

## CI / smoke mode (no keys)

```bash
python eval/run_golden_set.py --mock --offline-judge
```

Uses stub “agent” answers and a **keyword-only** judge (not a substitute for the LLM judge in the rubric). Useful to verify the harness in CI.

## Environment variables

| Variable | Default | Notes |
|----------|---------|--------|
| `POCKET_MECHANICS_API_URL` | `http://127.0.0.1:8000` | Backend base URL (no `/api` suffix). |
| `OPENROUTER_KEY` | _(required for LLM judge)_ | OpenRouter API key. |
| `JUDGE_MODEL` | `google/gemini-2.5-flash` | OpenRouter model id for the judge. |
