# Pocket Mechanics

Capstone project (**CS-AI-2025 / Spring 2026**): a web app that helps **non-mechanic car owners** identify parts from **engine-bay photos** and get **safety-aware maintenance guidance** (multimodal AI + optional car profile).

## Repo layout

| Path | Purpose |
|------|---------|
| `Frontend/` | Web UI (scaffold) |
| `Backend/` | FastAPI — **Lab 5** text-only `POST /api/ai/generate` (see `Backend/README.md`) |
| `docs/design-review/` | **Design Review** submission (`DESIGN-REVIEW.md`, `architecture-diagram.png`) |
| `lab-3/` | Lab 3 artifacts (e.g. `generation-strategy.md`) |
| `docs/lab-6.md` | **Lab 6** — streaming, session memory, MCP |
| `docs/lab-7.md` | **Lab 7** — agent architecture, resilience, LangGraph proof |
| `docs/agent-architecture-lab7.md` | **Lab 7** — pattern choice, AgentState, safety |
| `Backend/agent/` | **Lab 7** — `AgentState` schema |
| `orchestration/langgraph_mini/` | **Lab 7** — two-node LangGraph proof (local) |
| `mcp-server/` | **Lab 6** — MCP stdio server (`ask_pocket_mechanics_tip` → calls running API) |
| `eval/` | **Lab 9** — `golden_set.json`, `run_golden_set.py`, `async_golden_set.py`, `results/` |
| `docs/lab-8.md` | **Lab 8** — production MCP, caching benchmark |
| `docs/lab-9.md` | **Lab 9** — golden set + hardening |
| `docs/safety-audit.md` | **Week 11** — six evidence areas |
| `docs/optimization-report.md` | **Lab 8** — caching / fallback benchmark |
| `docs/metrics-report.md` | **Lab 9** — episode log metrics |
| `scripts/metrics_report.py` | Computes six metrics from episode log |
| `tests/` | Integration tests |

## Model selection decisions (Lab 9)

| Call / endpoint | Task type | Model | Why |
|-----------------|-----------|-------|-----|
| `POST /api/ai/generate` | Multimodal Q&A, vision | `google/gemini-2.5-flash` (OpenRouter) | Vision + cost; team default |
| `POST /api/ai/stream` | Interactive chat | Same as routing env | One stack; session memory |
| OpenRouter fallback | Degraded availability | `google/gemma-3-27b-it:free`, `meta-llama/llama-4-maverick:free` | Free tier when primary fails |
| Prompt cache benchmark | Stable system prefix | `anthropic/claude-haiku-4-5-20251001` | Anthropic `cache_control` support |
| Golden set judge | Deterministic pass/fail | `google/gemini-2.5-flash` | Cheap, JSON-friendly judge |
| MCP tool | Delegated maintenance tip | Uses backend `/api/ai/generate` | Single source of truth |

## Agent architecture (Lab 7)

Pocket Mechanics uses a **single-agent** design with explicit **`AgentState`**, **timeouts + exponential backoff** on LLM calls (`Backend/services/resilience.py`), and a **human approval gate** for hands-on repair questions on the stream API.

Details: **`docs/agent-architecture-lab7.md`** · Runbook: **`docs/lab-7.md`**

## Design Review

Main document: **`docs/design-review/DESIGN-REVIEW.md`**

Team contract: **`TEAM-CONTRACT.md`** (repo root)

## Setup

1. **Backend (AI endpoint):** `cd Backend` → copy `Backend/.env.example` to `Backend/.env` → set **`GEMINI_API_KEY`** (Google AI Studio) and/or **`OPENROUTER_KEY`** → `uv sync` → `uv run uvicorn main:app --reload --port 8000`. Docs: [http://localhost:8000/docs](http://localhost:8000/docs).
2. Root `.env.example` / keys: never commit `.env`.
3. See `docs/design-review/DESIGN-REVIEW.md` for architecture, data flow, safety, and governance.

## License / course

Course submission for KIU CS-AI capstone; see `TEAM-CONTRACT.md` for team agreement.
