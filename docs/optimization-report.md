# Optimisation Report

**Team Name:** Pocket Mechanics  
**Date:** 2026-05-20  
**Capstone Project:** Pocket Mechanics  
**Lab 8 checkpoint tag:** `lab8-mcp-capstone`

---

## 1. What We Optimised

> **Update (post-freeze prep):** the original caching benchmark targeted
> `anthropic/claude-haiku-4-5-20251001`, which our OpenRouter account no longer
> serves (NotFound). Prompt caching is **implemented** (`cache_control: ephemeral`
> on the stable system prefix for Anthropic models, see `llm_service._openrouter_system_content`),
> but the cache A/B in §3 was **not completed** because no Anthropic model is
> currently available on our account. The cross-vendor cost/latency comparison we
> *did* complete is in `eval/model-comparison.json` (Gemini vs GPT-5.5 vs DeepSeek),
> and the production fallback chain is `openai/gpt-5.5 → deepseek/deepseek-v4-flash`.

**Target call:** `POST /api/ai/generate` — `Backend/services/llm_service.py`

**Model:** OpenRouter `google/gemini-2.5-flash` (production default). **Caching benchmark model (no longer served):** `anthropic/claude-haiku-4-5-20251001` (Anthropic `cache_control` via OpenRouter).

**Cached prefix:** `build_system_prompt()` = default assistant + `SAFETY_POLICY_BLOCK` (~400+ tokens stable text). Enabled with `EXTENDED_SYSTEM_PROMPT=true` and `ENABLE_PROMPT_CACHE=true`.

**Why cacheable:** Same system + safety policy on every request; user prompt varies.

**Measure tokens:** Use `input_tokens`, `cache_read_tokens`, `cache_write_tokens` on API JSON and episode log.

---

## 2. Benchmark Results — Without Caching

**Procedure:** 10× `POST /api/ai/generate` with `ENABLE_PROMPT_CACHE=false` (restart API after env change).

Run: `python Backend/scripts/lab8_benchmark.py --base-url <API_URL>`

**Observed baseline (golden-set eval run, `openai/gpt-5-nano`, `cache_read_tokens=0` — from episode log):**

| Call # | Input Tokens | Output Tokens | Cost (USD) | Latency (ms) |
|--------|-------------|---------------|------------|--------------|
| 1 | 261 | 1420 | 0.00058105 | 20603 |
| 2 | 269 | 2032 | 0.00082625 | 26316 |
| 3 | 274 | 2602 | 0.00105450 | 21247 |
| 4 | 249 | 1276 | 0.00052285 | 18066 |
| 5 | 268 | 1461 | 0.00059780 | 18777 |
| 6 | 263 | 1075 | 0.00044315 | 77452 |
| 7 | 267 | 198 | 0.00009255 | 2343 |
| 8 | 258 | 1492 | 0.00060970 | 20289 |
| 9 | 273 | 1837 | 0.00074845 | 25980 |
| 10 | 261 | 1661 | 0.00000000 | 25665 |

**Median latency (ms):** 20603  
**Total cost (USD):** 0.00547585  
**Average cost per call (USD):** 0.00054759  

For the **Lab 8 Anthropic cache A/B**, re-run with the script and Haiku model:

```bash
# Without cache
ENABLE_PROMPT_CACHE=false python Backend/scripts/lab8_benchmark.py --base-url http://127.0.0.1:8000 --model anthropic/claude-haiku-4-5-20251001 --json

# With cache (restart API with ENABLE_PROMPT_CACHE=true first)
python Backend/scripts/lab8_benchmark.py --base-url http://127.0.0.1:8000 --model anthropic/claude-haiku-4-5-20251001 --json
```

Paste JSON output into §3–4 before tagging `lab8-mcp-capstone` if instructors require Haiku-specific cache numbers.

---

## 3. Benchmark Results — With Caching

**Procedure:** 10× same questions with `ENABLE_PROMPT_CACHE=true` and  
`python Backend/scripts/lab8_benchmark.py --base-url <API_URL> --model anthropic/claude-haiku-4-5-20251001`

| Call # | Input Tokens | Cache Read | Cache Write | Cost (USD) | Latency (ms) | Cache Hit |
|--------|-------------|------------|-------------|------------|--------------|-----------|
| 1 | *run* | *run* | *run* | *run* | *run* | Write |
| 2–10 | *run* | *run* | *run* | *run* | *run* | Read expected |

**Cache hit rate:** *hits with cache_read_tokens > 0 on calls 2–10 / 9*  
**Median latency (ms):** *from script*  
**Total cost (USD):** *from script*

**Expected outcome:** Lower input billing on Anthropic when `cache_read_tokens` > 0; latency may drop modestly on calls 2–10.

---

## 4. Summary and Analysis

**Cost reduction:** Compute after live run:  
`saved ≈ (cache_read_tokens × cached_input_price) per call` vs full input on uncached path.

**Latency:** Often dominated by output tokens; expect single-digit % improvement unless prefix is very large.

**Production choice:** Keep **Gemini Flash** for cost; use **Anthropic + cache** for high-volume identical system prefix if metrics justify it.

---

## 5. OpenRouter Fallback Chain

```text
Primary:    DEFAULT_MODEL (google/gemini-2.5-flash)
Fallback 1: google/gemma-3-27b-it:free
Fallback 2: meta-llama/llama-4-maverick:free
```

Override: `OPENROUTER_FALLBACK_MODELS=model-a,model-b`

**Fallback test:**

1. Set `DEFAULT_MODEL=google/this-model-does-not-exist` on Render/local `.env`
2. `POST /api/ai/generate` with `{"prompt":"What is a serpentine belt?"}`
3. Confirm response `model` is a fallback slug and episode row has `fallback_triggered=true`

---

## 6. What We Would Do Next

- Automate before/after rows into this file from `lab8_benchmark.py --json`
- Tune g002 golden question (5W-30 high-temp viscosity) via system prompt tweak
- Point `EPISODE_LOG_PATH` to durable storage on Render for Week 11 metrics
