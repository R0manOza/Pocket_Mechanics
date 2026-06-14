# Repository Review — Self-Assessment

**Team:** Pocket Mechanics (Roman Gurgenidze · Tornike Emnadze · Levan Mosiashvili)
**Assessed against:** Final Repo Checklist, CS-AI-2025.
**Legend:** ✅ done & verified · 🟡 partial · ⬜ todo · ⚠️ team action remaining

## Hard gates (pass/fail — fail caps the score)

| Gate | Status | Evidence / note |
|------|--------|-----------------|
| No secrets in git history | ✅ | A previously-committed Gemini key was revoked (Google auto-disabled it); documented in README "Security note". `sk-or-` grep is clean. |
| `Dockerfile` builds & runs from clean checkout | ✅ | `docker build` + `docker run` verified live: Uvicorn up, `/health` → 200, HEALTHCHECK green. python:3.11-slim, non-root. |
| `GET /health` < 500 ms, no LLM call | ✅ | `Backend/main.py` returns `{"status":"ok"}`; load test measured p99 30 ms under 50-user load. |
| CI green on main | ✅ | `.github/workflows/ci.yml` (tests + golden gate @0.70) ran green on PR. |
| `eval/results/` ≥ 3 committed run files | ✅ | 18 result files committed. |

## Evaluation

| Item | Status | Note |
|------|--------|------|
| `eval/golden_set.json` (3 factual / 2 reasoning / 2 edge / 2 refusal / 1 format) | ✅ | Rebalanced to the exact required mix. |
| `eval/run_golden_set.py` runs < 3 min, ≥ 7/10 | ✅ | Offline-judge gate green in CI. |
| `eval/model-comparison.json` (3+ models, 5+ Qs) | ✅ | gemini-2.5-flash / gpt-5.5 / deepseek-v4-flash, 5 Qs each, real latency + cost. |
| ≥ 3 result files committed | ✅ | 18 files. |

## Production engineering

| Item | Status | Note |
|------|--------|------|
| `ci.yml` golden gate @0.70, key in Secrets | ✅ | `OPENROUTER_API_KEY` from Secrets, not hardcoded. |
| `Dockerfile` non-root + HEALTHCHECK + python:3.11-slim | ✅ | Verified live. |
| Rate limiter → structured 429 with `retry_after_seconds` | ✅ | Verified live: 35-call burst → `{"error":"rate_limited","retry_after_seconds":4}`. |
| Fallback chain from `.env` (not hardcoded) | ✅ | `OPENROUTER_FALLBACK_MODELS` → `openai/gpt-5.5` → `deepseek/deepseek-v4-flash` (valid, account-served). |
| Every API response includes `model_used` | ✅ | Verified live on `/api/ai/generate` (`model_used: google/gemini-2.5-flash`) + stream path. |
| Episode log has `model_used` + `fallback_triggered` | ✅ | Logger writes both; existing `episode-log.jsonl` migrated (0 entries missing). |

## Load test & red team

| Item | Status | Note |
|------|--------|------|
| `load/locustfile.py` | ✅ | Ran 50 users / 2 min. |
| `load/load-test-report.md` with real p50/p95/p99 | ✅ | 2,764 reqs, 0 failures; generate p95 850 ms / p99 4.2 s; `/health` p99 30 ms. |
| 4 red-team attacks in `docs/safety-audit.md` | ✅ | injection / indirect / jailbreak / exfiltration — each with exact input, **verbatim live model output**, control that held. All refused. |

## Videos & Demo Day

| Item | Status | Note |
|------|--------|------|
| 2-min narrated demo video in README | ✅ | Recorded (~2:00), linked in README + case-study, shared "anyone with link". |
| 60-sec launch video | ✅ | Recorded, linked in README, shared "anyone with link". |
| 8-slide deck rehearsed, fits 10 min | ✅ | Slides linked; rehearse before 16:00. |

## Documentation

| Item | Status | Note |
|------|--------|------|
| `docs/safety-audit.md` (6 areas + red-team) | ✅ | 6 areas + Lab 12 red-team with live verbatim outputs. |
| `docs/case-study.md` (2–3 pages) | ✅ | Problem/approach/results/lessons; real numbers + live URL. |
| README model-selection table (task/model/reason/fallback/cost) | ✅ | Measured costs + cross-vendor table. |
| `AGENTS.md` | ✅ | At repo root. |
| `docs/ARCHITECTURE.md` | ✅ | System diagram + flows. |
| `docs/DEPLOYMENT.md` | ✅ | Vercel + Render runbook, correct URLs. |
| `docs/data-map.md` | ✅ | Present. |
| `docs/metrics-report.md` (6 metrics + thresholds) | ✅ | Present. |
| `docs/optimization-report.md` | ✅ | Completed model-selection optimisation with real before/after numbers (Gemini chosen: ~28× cheaper + ~1.9× faster than GPT-5.5). Prompt-caching A/B noted as not completed (target model no longer served) — no fabricated numbers. |

## Whole-repo completeness

| Item | Status | Note |
|------|--------|------|
| `.env.example` all vars + `.gitignore` lists `.env` | ✅ | Root + Backend complete; `.env` gitignored. |
| `TEAM-CONTRACT.md` signed | ✅ | Present. |
| `DESIGN-REVIEW.md` no `[fill in]` left | ✅ | No literal `[fill in]` placeholders (checklist UI boxes only). |
| `agent-architecture-lab7.md` (pattern, typed AgentState, guards) | ✅ | Present. |
| `logs/episode-log.jsonl` 100+ entries, zero PII | ✅ | 139 entries at root path; `model_used` + `fallback_triggered` present; no PII. |
| `mcp-server/` auth + validation + sanitized errors | ✅ | Area 3 scored 2/2 in Week 11 audit. |
| Live deployment (frontend + backend) | ✅ | Frontend https://pocket-mechanics.vercel.app/ · Backend https://pocket-mechanics.onrender.com/health → 200. |
| 4 lab tags pushed | ✅ | `lab9-hardening`, `lab10-production`, `lab11-portability`, `lab12-demo-day` all pushed at the final main commit (plus `lab7`/`lab8`). |
| Commits spread across semester per member | ✅ | Git history spans the term. |

## Status

All repository deliverables are complete and on `main`; all 6 lab tags are pushed.

Remaining items are operational (Demo Day), not repository content:
1. ⚠️ **Rebuild/redeploy the backend** so the model picker (3 working models), rate limiter, and `model_used` changes are live for the demo.
2. ⚠️ Rehearse the deck within the 10-minute slot.
