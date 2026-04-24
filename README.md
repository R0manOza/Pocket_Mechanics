# Pocket Mechanics

Capstone project (**CS-AI-2025 / Spring 2026**): a web app that helps **non-mechanic car owners** identify parts from **engine-bay photos** and get **safety-aware maintenance guidance** (multimodal AI + optional car profile).

## Repo layout

| Path | Purpose |
|------|---------|
| `Frontend/` | Web UI (scaffold) |
| `Backend/` | FastAPI — **Lab 5** text-only `POST /api/ai/generate` (see `Backend/README.md`) |
| `docs/design-review/` | **Design Review** submission (`DESIGN-REVIEW.md`, `architecture-diagram.png`) |
| `lab-3/` | Lab 3 artifacts (e.g. `generation-strategy.md`) |
| `docs/lab-6.md` | **Lab 6** — how to run streaming, session memory, MCP, and checkpoints |
| `mcp-server/` | **Lab 6** — MCP stdio server (`ask_pocket_mechanics_tip` → calls running API) |
| `tests/` | Tests (placeholder) |

## Design Review

Main document: **`docs/design-review/DESIGN-REVIEW.md`**

Team contract: **`TEAM-CONTRACT.md`** (repo root)

## Setup

1. **Backend (AI endpoint):** `cd Backend` → copy `Backend/.env.example` to `Backend/.env` → set **`GEMINI_API_KEY`** (Google AI Studio) and/or **`OPENROUTER_KEY`** → `uv sync` → `uv run uvicorn main:app --reload --port 8000`. Docs: [http://localhost:8000/docs](http://localhost:8000/docs).
2. Root `.env.example` / keys: never commit `.env`.
3. See `docs/design-review/DESIGN-REVIEW.md` for architecture, data flow, safety, and governance.

## License / course

Course submission for KIU CS-AI capstone; see `TEAM-CONTRACT.md` for team agreement.
