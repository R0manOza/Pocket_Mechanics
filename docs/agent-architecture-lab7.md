# Agent architecture — Lab 7 (Pocket Mechanics)

## Pattern: single agent (justified)

We use a **single multimodal assistant** with one optional **MCP tool** (`ask_pocket_mechanics_tip`), not a multi-agent crew.

**Why not orchestrator/supervisor/multi-agent?**

- User flows are linear: upload photo → ask → get guidance, or chat with session memory.
- Adding delegate agents would duplicate the same vision+language call without clearer ownership.
- Failure modes are simpler to reason about (one timeout/retry policy in `resilience.py`).

**Where orchestration appears**

- **LangGraph proof** (`orchestration/langgraph_mini/`) models a future **peer pipeline**: `research` → `write` → optional `human_review`.
- Production API maps those stages onto one model call plus explicit `AgentState` fields.

## AgentState

Defined in `Backend/agent/state.py`:

| Field | Purpose |
|-------|---------|
| `session_id` | Conversation id (frontend `localStorage`) |
| `user_request` | Latest user message |
| `messages` | OpenAI-style history (trimmed in `session_service`) |
| `current_step` | `idle`, `load_session`, `research`, `generate`, `await_approval`, `respond`, `done`, `error` |
| `approval_required` | True for hands-on repair phrasing |
| `approved` | User confirmed via `repair_steps_approved` on stream API |
| `retry_count` | Retries used on last external AI call |
| `timeout_ms` | Configured LLM timeout |
| `last_error` | Last failure label |
| `vehicle_context` | Domain: year/make/model hint |
| `research_notes` / `draft_answer` | Used in LangGraph proof; reserved for richer pipelines |

## Resilience

- **Module:** `Backend/services/resilience.py`
- **Every blocking LLM call** (`llm_service.generate`): `call_with_resilience` with exponential backoff.
- **Stream start** (`stream_router`): same wrapper around `create(stream=True)` / Gemini stream start.
- **Env:** `LLM_TIMEOUT_SECONDS`, `LLM_MAX_ATTEMPTS`, `LLM_BACKOFF_BASE_SECONDS`, `LLM_BACKOFF_CAP_SECONDS` (see `Backend/.env.example`).
- OpenRouter SDK still sets `timeout` and `max_retries`; our wrapper adds bounded backoff and episode logging.

## Safety checkpoints

**No irreversible automation today.** The API only returns text; it does not send email, charge cards, or write Firestore on behalf of the model.

**High-stakes UX gate:** If the user asks for procedural repair work (see `_HIGH_STAKES_MARKERS` in `agent/state.py`), `POST /api/ai/stream` sets `approval_required` and blocks the model until the client sends `repair_steps_approved: true`. The UI can add a confirm button later (Vercel frontend).

**Product safety:** `SafetyBanner` still warns users to verify with a mechanic.

## Episode log (Lab 7 fields)

`Backend/services/episode_logger.py` — CSV columns include `retry_count`, `timeout_ms`, `error`, `success` on `llm_call`, `stream_end`, and `error` events.

## Deployment note (Render / Vercel)

- **Render (backend):** Deploy as usual; set env vars on the Render service (no LangGraph on the server unless you choose to).
- **Vercel (frontend):** No change required for Lab 7 minimum; optional: send `repair_steps_approved` and `vehicle_context` in stream JSON body.

## Checkpoint

```bash
git tag lab7-agent-architecture-checkpoint
```
