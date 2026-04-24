"""
Pocket Mechanics API — Lab 5 text-only prototype (Gemini direct and/or OpenRouter).
"""

from pathlib import Path

from dotenv import load_dotenv

_backend = Path(__file__).resolve().parent
_repo = _backend.parent
# Repo root .env first, then Backend/.env overrides (GEMINI_API_KEY, OPENROUTER_KEY, etc.).
load_dotenv(_repo / ".env")
load_dotenv(_backend / ".env", override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import ai_router, stream_router

app = FastAPI(
    title="Pocket Mechanics API",
    description="Capstone API — Lab 5 blocking generate + Lab 6 SSE stream + session memory",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router.router, prefix="/api")
app.include_router(stream_router.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
