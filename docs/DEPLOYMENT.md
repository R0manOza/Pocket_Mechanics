# Pocket Mechanics — Deployment

This is the operational runbook for deploying Pocket Mechanics end-to-end.
Two services, deployed independently:

- **Frontend** → Vercel (static SPA, built by Vite)
- **Backend** → Render (FastAPI, `uvicorn`, `uv`)

CI/CD lives in [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml).
Pushes to `main` trigger blue-green deploys — but only for the surface(s) that
actually changed (scope is detected per push, so a frontend-only change
doesn't redeploy the backend).

> System overview: [`ARCHITECTURE.md`](ARCHITECTURE.md).
> Backend env reference: [`../Backend/.env.example`](../Backend/.env.example).

---

## 1. One-time provisioning

### 1.1 Render (backend)

1. Create a new **Web Service** in Render from the GitHub repo.
2. **Root directory:** `Backend`.
3. **Build command:**
   ```bash
   pip install uv && uv sync
   ```
4. **Start command:**
   ```bash
   uv run uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. **Health check path:** `/health`
6. **Auto deploy:** disabled. CI/CD triggers Render via API (see §2.2).
7. **Environment variables** (Render → Service → Environment): set the keys from [`Backend/.env.example`](../Backend/.env.example). Minimum:
   - `GEMINI_API_KEY` *or* `OPENROUTER_KEY` (at least one)
   - `DEFAULT_MODEL` (e.g. `google/gemini-2.5-flash`)
   - `ENABLE_PROMPT_CACHE=true`
   - Optional: `OPENROUTER_FALLBACK_MODELS`, `LLM_MAX_ATTEMPTS`, `MAX_VISION_IMAGES`, etc.

### 1.2 Vercel (frontend)

1. Create a Vercel project pointed at the GitHub repo.
2. **Root directory:** `Frontend`.
3. **Framework preset:** Vite.
4. **Build command:** (auto) `npm run build`
5. **Output directory:** (auto) `dist`
6. **Environment variables** (Vercel → Project → Settings → Environment Variables):
   - `VITE_API_BASE_URL` = the Render backend origin from §1.1, no trailing slash. Production: `https://pocket-mechanics.onrender.com`
7. (Optional) **Deployment Protection** → "Protection Bypass for Automation" → save the token as `VERCEL_PROTECTION_BYPASS` secret in GitHub so CI smoke-checks bypass the auth wall.

### 1.3 Backend CORS allow-list

In `Backend/main.py`, append the production Vercel origin (and your Vercel preview domain) to the CORS allow-list, or set `FRONTEND_ORIGINS` env if you've wired it through env. Localhost (`http://localhost:5173`) stays in for dev.

### 1.4 GitHub repo secrets

Settings → Secrets and variables → Actions → **New repository secret**.

| Secret | Where to find it | Used by |
|--------|------------------|---------|
| `RENDER_API_KEY` | Render → Account Settings → API Keys | Backend deploy job |
| `RENDER_SERVICE_ID` | Render service URL: `https://dashboard.render.com/web/srv-XXXX` | Backend deploy job |
| `RENDER_HEALTH_URL` | `https://<service>.onrender.com/health` | Post-deploy probe |
| `VERCEL_TOKEN` | Vercel → Account Settings → Tokens | Frontend deploy job |
| `VERCEL_ORG_ID` | Vercel → Team → Settings → General | Frontend deploy job |
| `VERCEL_PROJECT_ID` | Vercel → Project → Settings → General | Frontend deploy job |
| `VERCEL_PRODUCTION_DOMAIN` | The bare domain (e.g. `pocket-mechanics.vercel.app`) | Smoke check |
| `VITE_API_BASE_URL` | Render backend origin | Build-time inject |
| `VERCEL_PROTECTION_BYPASS` | Vercel → Deployment Protection (optional) | Smoke check |

---

## 2. Automated deploy (CI/CD)

Every push to `main` runs `.github/workflows/ci-cd.yml`:

1. **Detect scope** — diff against the previous commit; sets `frontend`/`backend` change flags.
2. **CI** — lint + build (frontend), pytest + coverage (backend).
3. **Validate build** — install `uv` + import smoke check (backend); produce `frontend-dist` artifact (frontend).
4. **Deploy** — only the surface(s) flagged by step 1:
   - **Frontend → Vercel:** `vercel pull --environment=production` → `vercel build --prod` → `vercel deploy --prebuilt --prod`.
   - **Backend → Render:** `POST https://api.render.com/v1/services/<id>/deploys` with the current `GITHUB_SHA`; then poll the deploy until status is `live` (timeout: 60 attempts × ~10s).
5. **Status check** — final job that gates the pipeline status.

### 2.1 Manual trigger

For a forced redeploy (no code change), make a no-op edit to one of the watched README files or use Render/Vercel dashboard.

### 2.2 Roll back

- **Render:** Dashboard → Deploys → pick a previous "live" deploy → **Redeploy**.
- **Vercel:** Dashboard → Deployments → pick a previous deploy → **Promote to Production**.

---

## 3. Manual deploy (without CI)

### 3.1 Backend (Render)

```bash
# From local — uses the Render API key
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache":"do_not_clear","commitId":"'"$(git rev-parse HEAD)"'"}' \
  "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys"
```

### 3.2 Frontend (Vercel)

```bash
cd Frontend
npm ci
npm install -g vercel@latest
vercel pull --yes --environment=production --token "$VERCEL_TOKEN"
vercel build --prod --token "$VERCEL_TOKEN"
vercel deploy --prebuilt --prod --token "$VERCEL_TOKEN"
```

---

## 4. Post-deploy verification

After each deploy, confirm:

```bash
# Backend health
curl -fsS https://<backend>.onrender.com/health   # → {"status":"ok"}

# Streaming endpoint smoke (text-only)
curl -N -X POST https://<backend>.onrender.com/api/ai/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"What is a serpentine belt?","session_id":"deploy-smoke"}'
```

Then open `https://<frontend>.vercel.app/chat`, send one message, confirm streaming.

If the frontend can't reach the backend:
- Check the browser network tab — does the request go to `VITE_API_BASE_URL`?
- Open the backend `/health` directly — is the service awake (Render free tier sleeps after inactivity)?
- Check `Backend/main.py` CORS allow-list contains the frontend origin.

---

## 5. Local development

See [`README.md`](../README.md#quick-start-local) for the local dev quickstart.
Local does **not** touch Vercel or Render — purely `uvicorn` + Vite on localhost.

---

## 6. Costs & quotas

- **OpenRouter:** shared project budget ~$30. Per-call cost is logged in `episode-log.csv` (`cost_usd`).
- **Render free tier:** sleeps after 15 min of inactivity; first request after sleep takes ~30–60 s.
- **Vercel hobby:** unlimited bandwidth for static SPA; serverless invocations not used (the SPA talks to Render directly).
- **GitHub Actions:** ~2,000 minutes/month free on private repos.

Set `MAX_VISION_IMAGES=2` and `MAX_VISION_BYTES_PER_IMAGE=5242880` (5 MB) to keep per-call image upload spend bounded — defaults in `.env.example`.
