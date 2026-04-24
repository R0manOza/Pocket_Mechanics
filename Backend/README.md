# Pocket Mechanics — Backend (Lab 5 + Lab 6)

- **Lab 5 — blocking:** `POST /api/ai/generate` → real model → JSON + `logs/cost-log.csv`
- **Lab 6 — streaming + memory:** `POST /api/ai/stream` (SSE) + in-memory sessions + `logs/episode-log.csv`

## Setup

```bash
cd Backend
cp .env.example .env
# Edit .env — set GEMINI_API_KEY (Google AI Studio) and/or OPENROUTER_KEY
```

**Gemini only (no OpenRouter):** put `GEMINI_API_KEY=...` in `Backend/.env` **or** in the repo root `.env` (both are loaded; `Backend/.env` wins if both exist). No other keys required.

**Both keys present:** OpenRouter is used by default. To force Gemini: set `USE_DIRECT_GEMINI=true`.

Install (uv recommended):

```bash
uv sync
```

Or: `pip install fastapi uvicorn[standard] openai python-dotenv pydantic google-generativeai`

## Run

From **`Backend/`** (so imports and `.env` resolve):

```bash
uv run uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs).

## Try it

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/api/ai/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\": \"What is a serpentine belt in one sentence?\"}"
```

(PowerShell: use `curl.exe` or single-line JSON.)

## Lab 5 checklist

- Real model response (not mocked)
- Cost log: `logs/cost-log.csv` — timestamp, model, tokens, latency, USD
- Tag: `lab5-checkpoint` after commit

Vision / image upload comes in a later iteration; this route is **text-only**.

---

## Lab 6 — streaming chat (SSE)

**`POST /api/ai/stream`** — `Content-Type: text/event-stream`

Body JSON:

```json
{
  "message": "What is a cabin air filter?",
  "session_id": "use-a-stable-uuid-per-chat",
  "system": "optional override",
  "model": "optional model override"
}
```

Example (PowerShell — **prefer file body**; inline JSON often breaks parsing):

```powershell
cd Backend
.\scripts\test-stream.ps1
```

Or manually:

```powershell
Set-Content -Path .\body.json -Value '{"message":"Hello","session_id":"test-1"}' -Encoding Ascii -NoNewline
curl.exe -N -X POST http://127.0.0.1:8000/api/ai/stream -H "Content-Type: application/json" --data-binary "@body.json"
```

Episode log (streaming + timing): **`logs/episode-log.csv`** (override with `EPISODE_LOG_PATH`).

Full write-up: **`docs/lab-6.md`**.
