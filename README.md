# Pocket Mechanics

Capstone project (**CS-AI-2025 / Spring 2026**): a web app that helps **non-mechanic car owners** identify parts from **engine-bay photos** and get **safety-aware maintenance guidance** (multimodal AI + optional car profile).

## Live demo

| Surface | URL |
|---------|-----|
| **Frontend (live)** | https://pocket-mechanics.vercel.app/ |
| **Backend API (Render)** | https://pocket-mechanics.onrender.com/ (`/docs` for OpenAPI, `/health` for liveness) |
| **2-min demo video** | https://drive.google.com/file/d/1feQyDSrqFqiTfF_F_NPPxPGjsy-2ithq/view?usp=sharing |
| **60-sec launch video** | https://drive.google.com/file/d/1tD41XDU9zPSjwKwZX26MW1_V0zaScEvj/view?usp=drive_link |
| **Presentation** | https://docs.google.com/presentation/d/1cBYYpPlSj6ee7Sv_kr2Mx4K6kHs5vqKN/edit?usp=drive_link |

> See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the step-by-step deployment runbook.
> **Note:** the Drive video and slides must be shared as "Anyone with the link → Viewer" to be publicly accessible.

## Features

- **Photo → part ID** — multimodal Q&A over an uploaded engine-bay photo (≤ 5 MB, JPEG/PNG/HEIC).
- **Streaming chat with memory** — SSE token streaming, session memory persisted across page reloads, multiple parallel chat sessions.
- **Safety-aware guidance** — refusal/redirect for unsafe requests; explicit gate on hands-on repair steps (`RepairApprovalBanner`).
- **Multi-vendor LLM routing** — OpenRouter (OpenAI, Anthropic, Llama, Gemma) with model fallback chain + direct Gemini path for dev.
- **Prompt caching** — Anthropic `cache_control: ephemeral` on stable system prefix (see `docs/optimization-report.md`).
- **MCP server** — `ask_pocket_mechanics_tip` stdio tool, bearer auth, Pydantic validation, JSONL audit log.
- **Eval + telemetry** — 30-case golden set with LLM-as-judge, episode log with cost / cache / latency / fallback fields.

## Tech stack

| Layer | Stack |
|-------|-------|
| Frontend | Vite 8 · React 19.2 · TypeScript 6 · Tailwind CSS v4 · React Router v6 |
| Backend | FastAPI (Python 3.12, `uv`) · Pydantic v2 · OpenAI SDK (OpenRouter) · `google-generativeai` |
| LLM providers | OpenRouter (OpenAI, Anthropic, Gemini, Llama, Gemma) · direct Gemini |
| MCP | stdio JSON-RPC · `modelcontextprotocol` SDK |
| Hosting | Vercel (frontend) · Render (backend) · CI/CD via GitHub Actions |
| Observability | CSV + JSONL episode log · MCP audit log · `scripts/metrics_report.py` |

## Quick start (local)

```bash
# Backend
cd Backend && cp .env.example .env  # fill in GEMINI_API_KEY and/or OPENROUTER_KEY
uv sync && uv run uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd Frontend && npm install && npm run dev   # http://localhost:5173
```

## Security note — secret handling

Early in the project a Gemini API key was accidentally committed to
`Backend/.env.example` (commits `fed10fb`, `65425ab`) before being replaced with
a placeholder on `184fe7a`. The exposed key was **revoked**: Google's automated
secret scanning detected the public key and disabled it, and we have since
confirmed it is dead and replaced it with a new key that lives only in
environment variables (`Backend/.env`, gitignored, and the deploy host's env).

We chose **not** to rewrite git history, because the leaked key is already
invalidated and rewriting would change every commit SHA — including
`7456456`, the SHA submitted for the Safety & Evaluation Audit. All current
secrets are kept out of version control: `.env*` is gitignored and
`.env.example` contains placeholders only.

## Screenshots

Screenshots live in [`docs/screenshots/`](docs/screenshots/) — landing page, chat with attached image, sessions sidebar, analyze page result card.

## Documentation

| Document | Purpose |
|----------|---------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System diagram + data flow |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Step-by-step Vercel + Render deployment |
| [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md) | Problem, design, AI implementation, results |
| [`docs/safety-audit.md`](docs/safety-audit.md) | Capstone Week 11 — six evidence areas |
| [`docs/optimization-report.md`](docs/optimization-report.md) | Lab 8 — caching + fallback benchmark |

---

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
| `docs/data-map.md` | **Week 11** — data governance / retention |
| `docs/evidence/` | Terminal captures for audit (MCP auth, isolation, git) |
| `docs/optimization-report.md` | **Lab 8** — caching / fallback benchmark |
| `docs/metrics-report.md` | **Lab 9** — episode log metrics |
| `scripts/metrics_report.py` | Computes six metrics from episode log |
| `tests/` | Integration tests |

## Model Selection Decisions

All model names are read from `.env` (`DEFAULT_MODEL`, `STREAM_MODEL`, `OPENROUTER_FALLBACK_MODELS`), never hardcoded. Cost is the measured average per query from `eval/model-comparison.json`.

| Task | Model | Reason | Fallback | Real cost |
|------|-------|--------|----------|-----------|
| `POST /api/ai/generate` (blocking Q&A) | `google/gemini-2.5-flash` (OpenRouter) | Vision + low cost for multimodal Q&A | `openai/gpt-5.5` → `deepseek/deepseek-v4-flash` | ~$0.00011 / query (measured) |
| `POST /api/ai/stream` (chat) | `STREAM_MODEL`, defaults to `google/gemini-2.5-flash` | One stack + session memory | same chain as above | ~$0.00011 / query |
| Prompt caching | Anthropic models (`cache_control` ephemeral) | Input-side savings on the stable safety prefix | n/a | see `docs/optimization-report.md` |
| Golden-set judge | `google/gemini-2.5-flash` (configurable) | Cheap JSON pass/fail | n/a (eval only) | negligible (eval runs only) |
| MCP `ask_pocket_mechanics_tip` | Delegates to `/api/ai/generate` | Single source of truth; inherits same model + fallback | inherits generate's chain | same as generate (~$0.00011) |

**Cross-vendor benchmark** (`eval/model-comparison.json`, 5 questions each):

| Model | Avg latency | Avg cost / query |
|-------|-------------|------------------|
| `google/gemini-2.5-flash` | 1,998 ms | $0.00011 |
| `deepseek/deepseek-v4-flash` | 3,519 ms | $0.000034 |
| `openai/gpt-5.5` | 3,749 ms | $0.0031 |

Gemini Flash wins on cost **and** latency, which is why it's the production default.

## Agent Architecture

### Pattern

**Single agent (justified).** Users follow one linear flow (photo and/or question → maintenance guidance). A supervisor/multi-agent setup would repeat the same multimodal call without clearer ownership. A **LangGraph proof** (`orchestration/langgraph_mini/`: research → write → human_review) documents how we could split stages later; production uses one model call plus explicit state and gates.

### AgentState

```python
@dataclass
class AgentState:
    session_id: str
    user_request: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    current_step: str = "idle"  # idle | load_session | research | generate | await_approval | respond | done | error
    approval_required: bool = False
    approved: bool = False
    retry_count: int = 0
    timeout_ms: int = 30_000
    last_error: str | None = None
    vehicle_context: str = ""
    research_notes: str = ""
    draft_answer: str = ""
```

Source: [`Backend/agent/state.py`](Backend/agent/state.py)

### Irreversible actions and guards

The API **does not** execute irreversible automation (no payments, account deletion, or Firestore writes from the model). User-facing risk is acting on **hands-on repair guidance**.

| Action | Risk | Checkpoint / guard |
|--------|------|-------------------|
| Following step-by-step repair instructions | Injury / vehicle damage | `approval_required_for_request()` sets `approval_required`; stream API blocks the model until `repair_steps_approved=true` |
| Relying on maintenance advice without verification | Wrong repair | `SafetyBanner` + system safety policy; model told to defer to manual/mechanic |
| Uploading engine-bay photos | Privacy (plates, reflections) | Upload disclosure; images not stored in Firestore by default |
| MCP tool calling backend generate | Unauthenticated use | Bearer token (`MCP_SECRET_KEY`) verified before tool logic |

Resilience: [`Backend/services/resilience.py`](Backend/services/resilience.py) — timeout + exponential backoff on every LLM call. Details: [`docs/agent-architecture-lab7.md`](docs/agent-architecture-lab7.md) · [`docs/lab-7.md`](docs/lab-7.md)

## Design Review

Main document: **`docs/design-review/DESIGN-REVIEW.md`**

Team contract: **`TEAM-CONTRACT.md`** (repo root)

## Setup

1. **Backend (AI endpoint):** `cd Backend` → copy `Backend/.env.example` to `Backend/.env` → set **`GEMINI_API_KEY`** (Google AI Studio) and/or **`OPENROUTER_KEY`** → `uv sync` → `uv run uvicorn main:app --reload --port 8000`. Docs: [http://localhost:8000/docs](http://localhost:8000/docs).
2. Root `.env.example` / keys: never commit `.env`.
3. See `docs/design-review/DESIGN-REVIEW.md` for architecture, data flow, safety, and governance.

## License / course

Course submission for KIU CS-AI capstone; see `TEAM-CONTRACT.md` for team agreement.
