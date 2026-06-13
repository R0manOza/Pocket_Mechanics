"""Available OpenRouter models with pricing for the frontend model picker."""

from __future__ import annotations

import os

from fastapi import APIRouter

from services import episode_logger

router = APIRouter()

# Human-readable labels for models we expose in the UI.
# Only models verified to be served by our OpenRouter account are listed, so the
# picker can never offer a model that 500s (NotFound) at request time.
_MODEL_LABELS: dict[str, str] = {
    "google/gemini-2.5-flash": "Gemini 2.5 Flash",
    "openai/gpt-5.5": "GPT-5.5",
    "deepseek/deepseek-v4-flash": "DeepSeek V4 Flash",
}

# Prefer OpenRouter ids (provider/model); skip short-name duplicates
_UI_MODEL_ORDER = [
    "google/gemini-2.5-flash",
    "openai/gpt-5.5",
    "deepseek/deepseek-v4-flash",
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
