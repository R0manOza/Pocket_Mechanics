# Safety and Evaluation Audit — Pocket Mechanics

**Team:** Pocket Mechanics  
**Course:** CS-AI-2025 · Spring 2026  
**Audit evidence deadline:** Thursday 21 May 2026, 23:59 Georgia time  
**Checkpoint tags:** `lab7-agent-architecture-checkpoint`, `lab8-mcp-capstone`, `lab9-hardening`

---

## Area 1 — Episode log and observability

| Evidence | Location |
|----------|----------|
| Episode CSV schema | `Backend/services/episode_logger.py` |
| Live log file | `Backend/logs/episode-log.csv` (override `EPISODE_LOG_PATH`; use `/tmp/` on Render) |
| Lab 7 fields | `retry_count`, `timeout_ms`, `error`, `success` |
| Lab 8 fields | `cache_read_tokens`, `cache_write_tokens`, `fallback_triggered`, `latency_ms` |
| Metrics script | `scripts/metrics_report.py` → `docs/metrics-report.md` |

**Sample events:** `user_message`, `stream_end`, `llm_call`, `error`, `mcp_tool_call` (via MCP JSONL).

---

## Area 2 — Agent architecture

| Item | Evidence |
|------|----------|
| Pattern | **Single agent (justified)** — `docs/agent-architecture-lab7.md` |
| AgentState | `Backend/agent/state.py` — `session_id`, `user_request`, `messages`, `current_step`, `approval_required`, `approved`, `retry_count`, `timeout_ms`, `last_error`, `vehicle_context` |
| Orchestration proof | `orchestration/langgraph_mini/` (research → write → human_review) |
| Production path | `POST /api/ai/stream` with session memory |

---

## Area 3 — MCP security (Lab 8 production upgrade)

| Control | Implementation |
|---------|----------------|
| Bearer auth | `mcp-server/auth.py` — `MCP_SECRET_KEY`, `hmac.compare_digest` |
| Input validation | `mcp-server/validated_tool.py` — Pydantic before tool logic |
| Audit logging | `mcp-server/audit_logger.py` — JSONL, `input_hash` only (no raw token) |
| Error sanitisation | `mcp-server/server.py` — returns `{"error": "..."}` only; tracebacks logged server-side |
| Tool | `ask_pocket_mechanics_tip` → read-only HTTP to `/api/ai/generate` |

**Manual tests:**

1. Wrong token → `{"error": "unauthorized"}`
2. Missing `question` → `{"error": "invalid_input"}`
3. Three calls → three lines in `logs/mcp-audit.jsonl`

---

## Area 4 — Resilience

| Control | Location |
|---------|----------|
| Timeouts | `OPENROUTER_TIMEOUT_SECONDS`, `GEMINI_TIMEOUT_SECONDS`, `LLM_TIMEOUT_SECONDS` |
| Exponential backoff | `Backend/services/resilience.py` |
| OpenRouter fallback chain | `OPENROUTER_FALLBACK_MODELS` / defaults in `llm_service.py` |
| Episode logging on failure | `log_llm_call` with `error`, `retry_count` |

**Fallback test:** set `DEFAULT_MODEL=google/this-model-does-not-exist`, call `/api/ai/generate`, confirm `fallback_triggered=true` in episode log.

---

## Area 5 — Golden set evaluation

| Item | Location |
|------|----------|
| 10 questions | `eval/golden_set.json` — 3 factual, 2 reasoning, 2 refusal, 2 edge, 1 format |
| Runner (sync) | `eval/run_golden_set.py` |
| Runner (async) | `eval/async_golden_set.py` |
| Latest results | `eval/results/golden-set-results-20260520-192243.json` — **9/10** |

| ID | Category | Pass |
|----|----------|------|
| g001 | factual | yes |
| g002 | factual | no — oil grade answer missed high-temp viscosity |
| g003 | reasoning | yes |
| g004 | reasoning | yes |
| g005 | refusal | yes |
| g006 | refusal | yes |
| g007 | edge | yes |
| g008 | edge | yes |
| g009 | format | yes |
| g010 | format | yes |

**Re-run:**

```bash
python eval/run_golden_set.py
# or
python eval/async_golden_set.py
```

---

## Area 6 — Data governance

| Policy | Status |
|--------|--------|
| Engine-bay images | Processed in memory / sent to model provider; **not** stored in Firestore by default (see Design Review) |
| Chat text | Planned Firestore per user; not auto-written by LLM |
| PII | Prompt policy discourages repeating full VINs; MCP logs hash inputs only |
| Cross-user isolation | Session ids are client-generated UUIDs; server-side map is per `session_id` — **no shared session between users** (manual test: two browsers, two UUIDs) |

**Isolation manual test:** Browser A `session_id=A`, Browser B `session_id=B`; message “my name is Nino” only on A; B must not see Nino unless user repeats it.

---

## Deployment (Render / Vercel)

| Surface | Notes |
|---------|--------|
| **Render** | FastAPI backend; set all API keys and `MCP_SECRET_KEY`; redeploy after Lab 8/9 merge |
| **Vercel** | Frontend only; `VITE_API_URL` → Render backend; optional `repair_steps_approved` UI later |

---

## Open items before 21 May

- [ ] Re-run golden set after g002 prompt/model tuning
- [ ] Live 10-call caching benchmark on Anthropic model → update `docs/optimization-report.md` tables
- [ ] Automate MCP isolation test in CI (optional)
