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
| `docs/data-map.md` | **Week 11** — data governance / retention |
| `docs/evidence/` | Terminal captures for audit (MCP auth, isolation, git) |
| `docs/optimization-report.md` | **Lab 8** — caching / fallback benchmark |
| `docs/metrics-report.md` | **Lab 9** — episode log metrics |
| `scripts/metrics_report.py` | Computes six metrics from episode log |
| `tests/` | Integration tests |

## Model Selection Decisions

| Call location | Current model | Reason for choice | Alternative considered |
|---------------|---------------|-------------------|------------------------|
| `POST /api/ai/generate` | `google/gemini-2.5-flash` (OpenRouter) or env default | Vision + cost for multimodal Q&A | `claude-sonnet-4-6`: higher cost |
| `POST /api/ai/stream` | Same as `DEFAULT_MODEL` / routing | One stack; session memory | Separate “fast” model: split behaviour |
| OpenRouter fallback chain | `google/gemma-3-27b-it:free`, `meta-llama/llama-4-maverick:free` | Availability when primary fails | Paid backup only: higher cost |
| Prompt cache benchmark | `anthropic/claude-haiku-4-5-20251001` | Anthropic `cache_control` on OpenRouter | Gemini: no equivalent cache fields |
| Golden set judge | `google/gemini-2.5-flash` (configurable) | Cheap JSON pass/fail | Larger judge model: slower eval |
| MCP `ask_pocket_mechanics_tip` | Delegates to `/api/ai/generate` | Single source of truth for answers | Duplicate model in MCP process |

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
