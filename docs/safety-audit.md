# Safety and Evaluation Audit — Pocket Mechanics

**Team:** Pocket Mechanics  
**Course:** CS-AI-2025 · Building AI-Powered Applications · Spring 2026  
**Evidence deadline:** Thursday 14 May 2026, 23:59 (Georgia time)  
**Live verification:** Friday 15 May 2026 — Week 11 lab (first 20 minutes)  
**Checkpoint tags:** `lab7-agent-architecture-checkpoint`, `lab8-mcp-capstone` (create after final commit)  
**Submit commit SHA:** 

---

## Area 1 — Episode log quality (2 pts)

| Evidence | Location |
|----------|----------|
| Episode log (CSV) | [`Backend/logs/episode-log.csv`](../Backend/logs/episode-log.csv) |
| Logger implementation | [`Backend/services/episode_logger.py`](../Backend/services/episode_logger.py) |
| Metrics helper | [`scripts/metrics_report.py`](../scripts/metrics_report.py) |

**Total entries (data rows, excluding header):** **139** (requirement: ≥ 100 from Lab 6 onward).

**Event types present:** `llm_call`, `stream_end`, `user_message`, `error`, `mcp_tool_call`.

### Five consecutive `llm_call` rows (all required Lab 8 fields)

From `Backend/logs/episode-log.csv` lines 118–122:

| session_id | event_type | model | input_tokens | output_tokens | cache_read_tokens | cache_write_tokens | latency_ms | fallback_triggered | error |
|------------|------------|-------|--------------|---------------|-------------------|--------------------|------------|--------------------|-------|
| api_generate | llm_call | openai/gpt-5-nano | 269 | 2032 | 0 | 0 | 26316 | False | *(empty)* |
| api_generate | llm_call | openai/gpt-5-nano | 274 | 2602 | 0 | 0 | 21247 | False | *(empty)* |
| api_generate | llm_call | openai/gpt-5-nano | 249 | 1276 | 0 | 0 | 18066 | False | *(empty)* |
| api_generate | llm_call | openai/gpt-5-nano | 268 | 1461 | 0 | 0 | 18777 | False | *(empty)* |
| api_generate | llm_call | openai/gpt-5-nano | 263 | 1075 | 0 | 0 | 77452 | False | *(empty)* |

`cache_read_tokens` is `0` when prompt caching is disabled or the model does not report cache hits (OpenAI `gpt-5-nano` path). Anthropic cache benchmark: see [`docs/optimization-report.md`](optimization-report.md).

### Error and fallback rows

| session_id | event_type | Notes |
|------------|------------|-------|
| audit_evidence | error | `error=RuntimeError`, `retry_count=2` — synthetic audit row |
| audit_evidence | llm_call | `fallback_triggered=True`, `error=ModelNotFound` — documents fallback logging |
| mcp | mcp_tool_call | `result_status=auth_failed`, `error=unauthorized` |

### MCP tool rows in episode log

| tool_name | result_status | input_hash | latency_ms |
|-----------|---------------|------------|------------|
| ask_pocket_mechanics_tip | ok | *(hash)* | 42 |
| ask_pocket_mechanics_tip | auth_failed | *(hash)* | 1 |
| ask_pocket_mechanics_tip | validation_failed | *(hash)* | 1 |

Regenerate audit rows: `python scripts/record_audit_evidence.py`

---

## Area 2 — Agent architecture documentation (1 pt)

| Evidence | Location |
|----------|----------|
| README section (required title) | [README § Agent Architecture](../README.md#agent-architecture) |
| Extended write-up | [`docs/agent-architecture-lab7.md`](agent-architecture-lab7.md) |
| AgentState source | [`Backend/agent/state.py`](../Backend/agent/state.py) |

**Pattern (one sentence):** We use a **single multimodal agent** with session memory and one MCP tool, because user flows are linear (photo/question → answer) and a multi-agent crew would duplicate the same vision+language work without clearer ownership.

**Irreversible actions:** The API does not perform irreversible side effects (no payments, email, or Firestore writes from the model). The highest-risk *user-facing* action is following **hands-on repair steps**; that is gated in software (see README table).

---

## Area 3 — MCP server security (2 pts)

| Control | Implementation |
|---------|----------------|
| Bearer auth | [`mcp-server/auth.py`](../mcp-server/auth.py) — `hmac.compare_digest`, secret from `MCP_SECRET_KEY` |
| Pydantic validation | [`mcp-server/validated_tool.py`](../mcp-server/validated_tool.py) |
| Audit JSONL | [`mcp-server/audit_logger.py`](../mcp-server/audit_logger.py) → [`logs/mcp-audit.jsonl`](../logs/mcp-audit.jsonl) |
| Sanitised errors | [`mcp-server/server.py`](../mcp-server/server.py) — `{"error": "<code>"}` only |

### Bad token — terminal output

```text
> python scripts/record_audit_evidence.py
[bad_token]
{"error": "unauthorized"}
```

Full capture: [`docs/evidence/mcp-auth-terminal.txt`](evidence/mcp-auth-terminal.txt)

### Pydantic schema (snippet)

```python
class PocketMechanicsTipInput(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    vehicle_hint: str = Field(default="", max_length=200)
    auth_token: str = Field(default="", alias="_auth_token")
```

### Sample MCP audit log entries (three lines)

From [`logs/mcp-audit.jsonl`](../logs/mcp-audit.jsonl):

```json
{"ts": 1779378432.1738563, "event_type": "mcp_tool_call", "tool_name": "ask_pocket_mechanics_tip", "input_hash": "b42bd4aa0ec28952", "result_status": "auth_failed", "latency_ms": 1, "error": "unauthorized"}
{"ts": 1779378432.1757479, "event_type": "mcp_tool_call", "tool_name": "ask_pocket_mechanics_tip", "input_hash": "38a088e1899e6c47", "result_status": "validation_failed", "latency_ms": 1, "error": "invalid_input"}
{"ts": 1779378391.0490072, "event_type": "mcp_tool_call", "tool_name": "ask_pocket_mechanics_tip", "input_hash": "7b8d0ed876cc24b1", "result_status": "error", "latency_ms": 2, "error": "tool_execution_failed"}
```

### Sanitised internal error

`tests/test_mcp_server.py::test_call_tool_sanitised_error` forces an internal failure; response is `{"error": "tool_execution_failed"}` with **no** traceback, file paths, or env var names. Pytest output: [`docs/evidence/mcp-pytest-output.txt`](evidence/mcp-pytest-output.txt).

**Live demo (lab):** Call MCP tool with `Authorization: Bearer wrong` → `{"error": "unauthorized"}`.

---

## Area 4 — Resilience patterns (1 pt)

**Applied to every blocking LLM call** in [`Backend/services/llm_service.py`](../Backend/services/llm_service.py) (`generate`) and **stream start** in [`Backend/routers/stream_router.py`](../Backend/routers/stream_router.py) via [`Backend/services/resilience.py`](../Backend/services/resilience.py).

### Timeout (OpenRouter client + Gemini request)

```python
_openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=key,
    timeout=float(os.environ.get("OPENROUTER_TIMEOUT_SECONDS", "30")),
    max_retries=int(os.environ.get("OPENROUTER_MAX_RETRIES", "2")),
)
```

Gemini: `request_options={"timeout": timeout_s}` on `generate_content`.

### Exponential backoff + bounded retries

```python
def backoff_seconds(attempt_index: int) -> float:
    base = float(os.environ.get("LLM_BACKOFF_BASE_SECONDS", "0.5"))
    cap = float(os.environ.get("LLM_BACKOFF_CAP_SECONDS", "8"))
    return min(cap, base * (2**attempt_index))
```

`call_with_resilience` logs each failed attempt to the episode log (`retry_count`, `error`) before retrying. OpenRouter also walks a **fallback model chain** in `generate()` with `fallback_triggered` on success after a prior model failed.

---

## Area 5 — Golden test set and evaluation (2 pts)

| Item | Location |
|------|----------|
| 10 questions | [`eval/golden_set.json`](../eval/golden_set.json) |
| Evaluation script | [`eval/run_golden_set.py`](../eval/run_golden_set.py) |
| Latest results | [`eval/results/golden-set-results-20260521-152758.json`](../eval/results/golden-set-results-20260521-152758.json) |

**Score: 10/10** (meets ≥ 7/10).

| ID | Category | Pass |
|----|----------|------|
| g001 | factual | yes |
| g002 | factual | yes |
| g003 | reasoning | yes |
| g004 | reasoning | yes |
| g005 | refusal | yes |
| g006 | refusal | yes |
| g007 | edge_case | yes |
| g008 | edge_case | yes |
| g009 | format | yes |
| g010 | format | yes |

**Re-run (lab demo):**

```bash
python eval/run_golden_set.py
```

Requires API at `http://127.0.0.1:8000` (or set base URL in script env). Completes in under 3 minutes with default judge model.

---

## Area 6 — Data governance (2 pts)

| Requirement | Evidence |
|-------------|----------|
| Data map | [`docs/data-map.md`](data-map.md) |
| Cross-user isolation | [`tests/test_session_service.py`](../tests/test_session_service.py) · output [`docs/evidence/isolation-test-output.txt`](evidence/isolation-test-output.txt) |
| PII-free logs | Sample below |
| No `.env` in git history | [`docs/evidence/git-env-check.txt`](evidence/git-env-check.txt) |

### Cross-user isolation — terminal output

```text
tests/test_session_service.py::TestSessionService::test_session_isolation PASSED [100%]
============================== 1 passed in 0.10s ==============================
```

User A’s messages are stored under `session-1`; User B’s `session-2` load returns only B’s content — **User B cannot retrieve User A’s data**.

Regenerate: `python scripts/capture_isolation_evidence.py`

### PII confirmation (episode log sample)

Recent `llm_call` rows contain **no** names, emails, or phone numbers — only `session_id` labels such as `api_generate`, `audit_evidence`, and `mcp`, plus token counts and model ids.

### API key security

```bash
git log --all -- .env Backend/.env
# (no commits — PASS)
```

---

## Lab 8 optimisation (Repository Review contribution)

| Document | Location |
|----------|----------|
| Caching / fallback benchmark | [`docs/optimization-report.md`](optimization-report.md) |
| Benchmark script | [`Backend/scripts/lab8_benchmark.py`](../Backend/scripts/lab8_benchmark.py) |

Run 10-call before/after with `ENABLE_PROMPT_CACHE` and Anthropic model per report instructions.

---

## Week 11 lab — live checklist (20 minutes)

1. `python eval/run_golden_set.py` → pass/fail summary  
2. MCP tool with invalid Bearer token → `{"error": "unauthorized"}`  
3. `python scripts/capture_isolation_evidence.py` or `pytest tests/test_session_service.py -k isolation` → PASSED  

---

## Evidence checklist (self-grade)

- [x] 100+ episode log entries  
- [x] LLM fields: `cache_read_tokens`, `latency_ms`, `fallback_triggered`  
- [x] MCP + error event types in episode log  
- [x] README **Agent Architecture** (four elements)  
- [x] MCP auth / validation / audit / sanitised errors documented  
- [x] Timeout + exponential backoff on all LLM calls  
- [x] Golden set 10/10, results file committed path listed  
- [x] Data map, isolation test, PII note, no `.env` in history  
- [ ] **You:** commit, push, tag `lab8-mcp-capstone`, submit form + SHA above  
