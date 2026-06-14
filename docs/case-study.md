# Case Study — Pocket Mechanics

**Team:** Roman Gurgenidze · Tornike Emnadze · Levan Mosiashvili
**Course:** Building AI-Powered Applications · CS-AI-2025 · Spring 2026 · KIU

> A 2–3 page account of what we built, why, how, what the numbers say, and what
> we learned.

---

## 1. Problem

Most car owners are not mechanics. When a warning light comes on or something
sounds wrong, their options are all poor:

- **Search engines** return forum threads written for mechanics — too technical,
  often contradictory, and with no safety framing for a novice.
- **A mechanic** costs money and time *before* the owner even knows whether the
  problem is urgent, so people delay — and small issues become expensive ones.
- **The owner's manual** is hundreds of pages of jargon nobody reads in a
  parking lot at night.

Our target user is someone like **Mariam, 22, who drives a 2014 Ford Focus and
panics at every warning light.** She needs a plain-language, safety-aware answer
in seconds — not a diagnosis she can't act on, and not a confident-but-wrong
instruction that could get her hurt.

The core product question: *can an AI assistant give genuinely useful,
safety-first car guidance — from a photo and a question — cheaply and reliably
enough to trust?*

## 2. Approach

We built a web app with two interaction modes:

1. **Streaming chat** — ask a question in natural language, get a token-by-token
   answer with memory across the conversation.
2. **Photo analysis** — attach an engine-bay photo and ask about it; a
   vision-capable model identifies parts and answers in context.

### Architecture (summary; full detail in `ARCHITECTURE.md`)

- **Frontend:** React 19 + Vite + TypeScript + Tailwind v4, deployed on Vercel.
- **Backend:** FastAPI (Python 3.11, `uv`) on Render, exposing
  `POST /api/ai/generate` (blocking), `POST /api/ai/stream` (SSE), and
  `GET /health`.
- **Provider abstraction:** every model call routes through one
  `llm_service` layer, so OpenRouter (Google, Meta, Anthropic, others) and a
  direct Gemini path are all reachable through a single code path — one
  resilience policy, one cost meter, one log schema.
- **MCP server:** the same backend is exposed as an MCP tool
  (`ask_pocket_mechanics_tip`) so other AI agents can use it — hardened with
  bearer auth, Pydantic validation, and a structured audit log.

### Key design decisions

- **Safety is centralized.** A `SAFETY_POLICY_BLOCK` system prompt enforces
  refusals (airbags, odometer fraud, medical-dose questions) and ends answers
  with a verify-with-a-professional note. Because the web app and the MCP tool
  both route through the same endpoint, the safety rules are identical no matter
  how the product is reached.
- **No database.** Sessions live in memory; each user's chat history stays on
  their own device (browser `localStorage`). This is a deliberate
  privacy-and-simplicity choice — there is no central store of user
  conversations to leak.
- **Resilience by default.** Every model call has a timeout, exponential
  backoff, and a multi-provider fallback chain (primary → secondary → OSS), all
  configured from `.env`.
- **Measure, don't guess.** A golden-set evaluation harness with an
  LLM-as-judge scores quality across five categories; results are committed so
  they're reproducible.

## 3. Results

| Metric | Result | Source |
|--------|--------|--------|
| Golden-set score (LLM-as-judge, 5 categories) | **10 / 10** | `eval/results/golden-set-results-20260521-152758.json` |
| Cost per query (production: Gemini 2.5 Flash) | **~$0.00011** | `eval/model-comparison.json` |
| Median answer latency (full, long replies) | **~22 s** | golden-set run (long, thorough answers) |
| p95 answer latency | **~28 s** | same run |
| Error rate in logged calls | **~2%** (3 / 151) | `Backend/logs/episode-log.csv` |
| Multi-provider fallback fired & recovered | **3×** | episode log (`fallback_triggered=true`) |
| Committed evaluation runs | **18** | `eval/results/` |
| Load test (50 users / 2 min) | **2,764 reqs, 0 failures**; `/health` p99 30 ms | `load/load-test-report.md` |

**Live app:** https://pocket-mechanics.vercel.app/ · **Launch video (60s):** https://drive.google.com/file/d/1tD41XDU9zPSjwKwZX26MW1_V0zaScEvj/view?usp=drive_link · **Slides:** https://docs.google.com/presentation/d/1cBYYpPlSj6ee7Sv_kr2Mx4K6kHs5vqKN/edit · **2-min demo video:** https://drive.google.com/file/d/1feQyDSrqFqiTfF_F_NPPxPGjsy-2ithq/view?usp=sharing

Notable: the fallback chain isn't theoretical — it fired and recovered three
times in our logs, and the user got an answer every time. The latency is honest:
full answers take ~22 s because they are long and thorough, but streaming shows
tokens from the first second, so there is no blank wait.

## 4. Challenges

- **Streaming + images.** Wiring server-sent events together with base64 image
  inputs (and HEIC→JPEG conversion client-side) was the hardest integration.
- **Silent failover.** Making the provider fallback switch *without* the user
  seeing an error flicker took several iterations of the resilience layer.
- **Two memories that can drift.** Browser history persists, but backend session
  memory is in-process and resets on restart — a known limitation we chose to
  accept for the capstone scope (the clean fix is Redis-backed sessions).
- **Cost is output-dominated.** Our answers are long, so generation cost
  dominates input cost — which is why prompt caching (an input-side
  optimization) yields only modest savings for our workload.

## 5. Lessons learned

- **A reliable AI product is ~20% the model and ~80% the hardening around it** —
  the retries, fallbacks, evals, refusals, and logging are the product, not an
  afterthought.
- **Centralizing safety pays off.** One safety policy, inherited by every entry
  point, beats scattering rules — and it made the safety audit straightforward.
- **Measure honestly.** Committing every eval run (not just the best one) and
  logging every call kept us from believing our own optimistic guesses; the real
  numbers (2% error, ~22 s latency) are less shiny than "0% / instant" but they
  hold up under scrutiny.
- **One abstraction, many providers.** Routing all calls through one
  `llm_service` made multi-vendor fallback, caching, and cost tracking a
  one-place change instead of a scattered rewrite.

## 6. What we'd build next

- Persistent car profiles (Firestore) and Redis-backed session memory.
- A native mobile camera flow for the photo feature.
- A real cache A/B on the Anthropic path to quantify prompt-cache savings.
