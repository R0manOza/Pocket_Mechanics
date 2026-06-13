# AGENTS.md — working in the Pocket Mechanics repo

Guidance for AI coding agents (and new human contributors). Read this before making changes.

## What this project is

Pocket Mechanics is a multimodal AI car-maintenance assistant: a user uploads an
engine-bay photo and/or asks a plain-language question, and gets safety-aware
guidance. FastAPI backend + React frontend, with an MCP tool, evaluation harness,
and resilience/observability built in.

## Repo map

| Path | What lives here |
|------|-----------------|
| `Backend/` | FastAPI app. Entry point `Backend/main.py` (`app`). |
| `Backend/routers/` | HTTP routes: `ai_router` (`/api/ai/generate`), `stream_router` (`/api/ai/stream`), `models_router` (`/api/models`). |
| `Backend/services/` | `llm_service` (provider abstraction + fallback + caching), `resilience` (timeout/backoff), `session_service` (in-memory memory), `episode_logger`, `vision_utils`, `system_prompts`. |
| `Backend/agent/` | `AgentState` dataclass (Lab 7). |
| `Frontend/` | Vite + React 19 + TypeScript + Tailwind v4 SPA. |
| `mcp-server/` | Stdio MCP server (`ask_pocket_mechanics_tip`) — bearer auth, Pydantic validation, audit log. |
| `eval/` | Golden set (`golden_set.json`), runner (`run_golden_set.py`), results (`results/`). |
| `tests/` | Pytest suite for the backend. |
| `orchestration/langgraph_mini/` | LangGraph proof (research → write → human_review). |
| `docs/` | Architecture, deployment, safety audit, case study, optimization & metrics reports. |
| `logs/` & `Backend/logs/` | Episode log (CSV + JSONL), cost log, MCP audit log. |
| `Dockerfile` | Backend container (python:3.11-slim, non-root, HEALTHCHECK). |
| `.github/workflows/` | `ci.yml` (tests + golden gate), `ci-cd.yml` (blue-green deploy). |

## How to run

### Backend
```bash
cd Backend
cp .env.example .env          # set GEMINI_API_KEY and/or OPENROUTER_KEY
uv sync
uv run uvicorn main:app --reload --port 8000   # http://localhost:8000/docs
```

### Frontend
```bash
cd Frontend
npm install
npm run dev                   # http://localhost:5173
```

### Docker (backend)
```bash
docker build -t pocket-mechanics .
docker run -p 8000:8000 --env-file Backend/.env pocket-mechanics
```

### Tests
```bash
cd Backend && uv run pytest ../tests -q
```

### Evaluation
```bash
# Deterministic, no key (used by CI):
python eval/run_golden_set.py --mock --offline-judge
# Real LLM-as-judge (needs OPENROUTER_KEY + running backend):
python eval/run_golden_set.py
```

## Conventions

- **Python 3.11+, `uv` for the backend.** Deps are declared in `Backend/pyproject.toml` — add deps there, not via ad-hoc pip.
- **Provider calls go through `services/llm_service.py` only.** Don't call OpenAI/Gemini SDKs directly from routers — use the abstraction so resilience, fallback, caching, and cost logging stay centralized.
- **Every model call is logged** to the episode log via `episode_logger`. Preserve the schema (model, tokens, cache, latency, fallback_triggered, error, retry_count).
- **No secrets in code or git.** Read from env (`os.environ`). `.env*` is gitignored; `.env.example` documents every variable.
- **Frontend uses Tailwind v4 `@theme` tokens** (`src/index.css`). Use `brand-*` color utilities, not raw hex. Prefer native Tailwind sizing utilities.
- **Safety is centralized** in `services/system_prompts.py` (`SAFETY_POLICY_BLOCK`). Don't scatter safety rules; both the web app and MCP tool inherit them because both route through `/api/ai/generate`.

## Guardrails for changes

- Don't break the `/health` endpoint contract (must respond fast, no LLM call).
- Don't remove episode-log fields — graded artifacts and `scripts/metrics_report.py` depend on the schema.
- Keep the golden set passing (≥ 7/10) — CI enforces it at the 0.70 threshold.
- When adding a model, set it via `.env` (`DEFAULT_MODEL`, `OPENROUTER_FALLBACK_MODELS`) — never hardcode model names in source.

## Where to look first

- API behavior → `Backend/routers/` + `Backend/services/llm_service.py`
- System/safety prompt → `Backend/services/system_prompts.py`
- Architecture overview → `docs/ARCHITECTURE.md`
- Deployment → `docs/DEPLOYMENT.md`
