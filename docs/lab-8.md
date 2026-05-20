# Lab 8 — MCP production + optimisation (Pocket Mechanics)

## Part 1 — MCP production (done in repo)

| Step | File(s) |
|------|---------|
| Bearer auth | `mcp-server/auth.py` |
| Pydantic validation | `mcp-server/validated_tool.py` |
| Structured audit JSONL | `mcp-server/audit_logger.py` |
| Sanitised errors | `mcp-server/server.py` |

**Env (Render + local):** `MCP_SECRET_KEY`, `POCKET_MECHANICS_API_URL`, optional `MCP_LOG_PATH`

**Test:**

```powershell
cd mcp-server
$env:MCP_SECRET_KEY="your-secret"
python server.py   # use Inspector in another terminal — do not type into stdio
```

## Part 2 — Caching + benchmark

| Item | Location |
|------|----------|
| Cache markup (Anthropic) | `llm_service._openrouter_system_content` when `ENABLE_PROMPT_CACHE=true` |
| Extended stable system prefix | `EXTENDED_SYSTEM_PROMPT=true` + `services/system_prompts.py` |
| Benchmark script | `Backend/scripts/lab8_benchmark.py` |
| Report | `docs/optimization-report.md` |

**Run benchmark (local or Render URL):**

```powershell
# Caching off — restart API with ENABLE_PROMPT_CACHE=false
python Backend/scripts/lab8_benchmark.py --base-url http://127.0.0.1:8000

# Caching on — ENABLE_PROMPT_CACHE=true and model anthropic/claude-haiku-4-5-20251001
python Backend/scripts/lab8_benchmark.py --base-url http://127.0.0.1:8000 --model anthropic/claude-haiku-4-5-20251001
```

**Fallback test:**

```text
DEFAULT_MODEL=google/this-model-does-not-exist
POST /api/ai/generate
→ episode log: fallback_triggered=true
```

## Tag

```bash
git tag lab8-mcp-capstone
git push origin main --tags
```

This tag is what the **Safety Audit** reads.
