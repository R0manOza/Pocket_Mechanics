"""Available OpenRouter models with pricing for the frontend model picker."""

from __future__ import annotations

import os

from fastapi import APIRouter

from services import episode_logger

router = APIRouter()

# Human-readable labels for models we expose in the UI
_MODEL_LABELS: dict[str, str] = {
    "google/gemini-2.5-flash": "Gemini 2.5 Flash",
    "google/gemini-2.5-pro": "Gemini 2.5 Pro",
    "anthropic/claude-haiku-4-5-20251001": "Claude Haiku 4.5",
    "anthropic/claude-sonnet-4-6": "Claude Sonnet 4.6",
    "openai/gpt-4o": "GPT-4o",
    "openai/gpt-5-nano": "GPT-5 Nano",
    "google/gemma-3-27b-it:free": "Gemma 3 27B (free)",
    "meta-llama/llama-4-maverick:free": "Llama 4 Maverick (free)",
}

# Prefer OpenRouter ids (provider/model); skip short-name duplicates
_UI_MODEL_ORDER = [
    "google/gemini-2.5-flash",
    "openai/gpt-5-nano",
    "openai/gpt-4o",
    "anthropic/claude-haiku-4-5-20251001",
    "anthropic/claude-sonnet-4-6",
    "google/gemini-2.5-pro",
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-4-maverick:free",
]


@router.get("/ai/models")
def list_models():
    default = os.environ.get("DEFAULT_MODEL", "google/gemini-2.5-flash")
    pricing = episode_logger.MODEL_PRICING
    models = []
    seen: set[str] = set()

    for model_id in _UI_MODEL_ORDER:
        if model_id not in pricing or model_id in seen:
            continue
        seen.add(model_id)
        p = pricing[model_id]
        models.append(
            {
                "id": model_id,
                "label": _MODEL_LABELS.get(model_id, model_id),
                "input_usd_per_million": p["input"],
                "output_usd_per_million": p["output"],
            }
        )

    return {"default": default, "models": models}
