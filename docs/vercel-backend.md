# Deploy backend to Vercel (FastAPI)

This repo includes a Vercel serverless entrypoint that exposes the existing FastAPI app:

- Entry: `api/index.py` (exports `app`)
- Routing: `vercel.json` routes all paths to `api/index.py`

## 1) Vercel project settings

1. Create a new Vercel project and import this GitHub repo.
2. Framework preset: **Other** (Python).

## 2) Environment variables

Set at least one of these in Vercel → Project → Settings → Environment Variables:

- `GEMINI_API_KEY` (recommended if you are not using OpenRouter)
- `GEMINI_MODEL` (optional, default: `gemini-2.5-flash`)

Optional (OpenRouter path):

- `OPENROUTER_KEY`
- `DEFAULT_MODEL` (default: `google/gemini-2.5-flash`)

Logging paths (optional):

- `COST_LOG_PATH` (default: `logs/cost-log.csv`)
- `EPISODE_LOG_PATH` (default: `logs/episode-log.csv`)

## 3) Deploy

Push to `main`. Vercel will build using:

- `requirements.txt` at repo root
- `api/index.py` as the serverless handler

## 4) Verify

After deploy:

- `GET /health` should return `{\"status\":\"ok\"}`
- `POST /api/ai/generate` should return JSON with `content`, token counts, etc.

## Important caveats (Vercel serverless)

- **Session memory is not durable.** Lab 6 sessions are stored in-process (`Backend/services/session_service.py`). Serverless instances restart, so sessions can disappear.
- **SSE streaming may be limited.** `POST /api/ai/stream` uses server-sent events. Some serverless environments buffer/timeout long-lived streams. If streaming is unreliable, deploy the backend to a long-running host (Railway/Fly/Render) instead.
- **Filesystem is read-only.** Vercel does not allow writing `logs/*` in the repo directory. This code falls back to `/tmp` (or stdout-only if file writing fails) for `cost-log.csv` and `episode-log.csv`.

