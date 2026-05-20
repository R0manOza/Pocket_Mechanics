# Optimisation Report

**Team Name:** Pocket Mechanics  
**Date:** 2026-05-20  
**Capstone Project:** Pocket Mechanics

---

## 1. What We Optimised

**Target call identified:** `POST /api/ai/generate`, implemented in `Backend/services/llm_service.py`.

**Model used for this call:** OpenRouter defaults to `google/gemini-2.5-flash`, with fallback models configured in code and optionally overridden through `OPENROUTER_FALLBACK_MODELS`.

**Approximate system prompt token count:** The default Pocket Mechanics system prompt is short, so provider caching only activates when the selected provider/model supports cache markup and the static prompt/context is large enough. Anthropic OpenRouter models receive `cache_control` markup automatically when `ENABLE_PROMPT_CACHE=true`.

**Reason this call is a caching candidate:** The system instruction is stable across repeated calls. If the project adds a larger static safety policy, repair knowledge base, or tool description block to that system context, the prefix can be cached while user prompts remain dynamic.

---

## 2. Benchmark Results - Without Caching

**Test procedure:** 10 consecutive calls to `/api/ai/generate` with `ENABLE_PROMPT_CACHE=false`.

| Call # | Input Tokens | Output Tokens | Cost (USD) | Latency (ms) |
|--------|-------------|---------------|------------|--------------|
| 1 | Pending live run | Pending live run | Pending live run | Pending live run |
| 2 | Pending live run | Pending live run | Pending live run | Pending live run |
| 3 | Pending live run | Pending live run | Pending live run | Pending live run |
| 4 | Pending live run | Pending live run | Pending live run | Pending live run |
| 5 | Pending live run | Pending live run | Pending live run | Pending live run |
| 6 | Pending live run | Pending live run | Pending live run | Pending live run |
| 7 | Pending live run | Pending live run | Pending live run | Pending live run |
| 8 | Pending live run | Pending live run | Pending live run | Pending live run |
| 9 | Pending live run | Pending live run | Pending live run | Pending live run |
| 10 | Pending live run | Pending live run | Pending live run | Pending live run |

**Median latency (ms):** Pending live run  
**Total cost (USD):** Pending live run  
**Average cost per call (USD):** Pending live run

---

## 3. Benchmark Results - With Caching

**Test procedure:** 10 consecutive calls to `/api/ai/generate` with `ENABLE_PROMPT_CACHE=true` and an Anthropic OpenRouter model or a large static Gemini cached context.

| Call # | Input Tokens | Cache Read Tokens | Cache Write Tokens | Cost (USD) | Latency (ms) | Cache Hit |
|--------|-------------|------------------|-------------------|------------|--------------|-----------|
| 1 | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run | Write |
| 2 | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run |
| 3 | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run |
| 4 | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run |
| 5 | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run |
| 6 | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run |
| 7 | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run |
| 8 | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run |
| 9 | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run |
| 10 | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run | Pending live run |

**Cache hit rate:** Pending live run  
**Median latency (ms):** Pending live run  
**Total cost (USD):** Pending live run  
**Average cost per call (USD):** Pending live run

---

## 4. Summary and Analysis

**Cost reduction:** Pending live benchmark.

**Latency change:** Pending live benchmark.

**Why latency changed (or did not change):** Expected gains are mainly in provider-side input processing. Output generation latency will still dominate longer answers.

**Tokens saved by caching per call:** Report `cache_read_tokens` from the episode log after the live benchmark.

---

## 5. OpenRouter Fallback Chain

**Fallback chain configured:**

```text
Primary:    DEFAULT_MODEL or request model
Fallback 1: google/gemma-3-27b-it:free
Fallback 2: meta-llama/llama-4-maverick:free
```

The fallback list can be overridden with:

```text
OPENROUTER_FALLBACK_MODELS=model-one,model-two
```

**Fallback test result:** Pending live run. To test, set `DEFAULT_MODEL=google/does-not-exist-model`, call `/api/ai/generate`, and confirm the response uses a fallback model while the episode log records `fallback_triggered=true`.

---

## 6. What We Would Do Next

Add a benchmark helper that drives the 10-call before/after procedure automatically, then switch the production default to the provider/model combination that shows the best cost and latency profile for Pocket Mechanics answers.

