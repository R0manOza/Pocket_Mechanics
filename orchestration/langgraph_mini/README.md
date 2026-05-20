# LangGraph mini-build (Lab 7)

Local proof only — **not deployed** to Render. Production chat still uses `POST /api/ai/stream` on the FastAPI backend.

## Install and run

```powershell
cd orchestration/langgraph_mini
pip install -r requirements.txt
python main.py
python main.py --high-stakes
python main.py --high-stakes --approved
```

You should see `[node:research]`, `[node:write]`, and for high-stakes requests without `--approved`, `[node:human_review]`.

## Capstone mapping

| Graph node | Production equivalent |
|------------|----------------------|
| `research` | Vision + context gathering (photo analyze, vehicle hint) |
| `write` | `llm_service.generate` / SSE stream |
| `human_review` | `approval_required` on `AgentState` + `repair_steps_approved` on stream API |
