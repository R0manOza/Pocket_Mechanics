# Lab 7 — Pocket Mechanics (implementation notes)

**Course:** Lab 7 — *Agents, Orchestration, Resilience, and Safety*

See **`docs/agent-architecture-lab7.md`** for the full architecture write-up.

---

## Quick verification (local)

### 1) Architecture + resilience

- Read `docs/agent-architecture-lab7.md`
- Run tests: `cd Backend && uv run pytest ../tests/test_resilience.py ../tests/test_agent_state.py -q`

### 2) Streaming with session memory (Lab 6 baseline)

```powershell
cd Backend
.\scripts\test-stream.ps1
```

Same `session_id` across five messages; agent should remember turn 1 in turn 5.

### 3) LangGraph mini-build (local only)

```powershell
cd orchestration\langgraph_mini
pip install -r requirements.txt
python main.py
python main.py --high-stakes
```

### 4) Episode log

After a stream or generate call, open `Backend/logs/episode-log.csv` (or `EPISODE_LOG_PATH`) and confirm `retry_count`, `timeout_ms`, and `error` columns on failure rows.

---

## Render / Vercel

| Surface | Lab 7 action |
|---------|----------------|
| **Render** | Redeploy backend after merge; add optional env: `LLM_MAX_ATTEMPTS`, `LLM_BACKOFF_BASE_SECONDS` (defaults work without them). |
| **Vercel** | No deploy required for passing Lab 7 backend criteria; optional frontend: `repair_steps_approved` + confirm UI for repair questions. |

---

## Git checkpoint

```bash
git add .
git commit -m "lab7: agent architecture, retries, checkpoint, langgraph mini-build"
git tag lab7-agent-architecture-checkpoint
git push origin main --tags
```
