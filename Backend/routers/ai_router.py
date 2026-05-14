from fastapi import APIRouter, HTTPException
from models.request_models import GenerateRequest, GenerateResponse
from services import llm_service

router = APIRouter()

_DEFAULT_SYSTEM = (
    "You are Pocket Mechanics, a beginner-friendly car maintenance assistant. "
    "Answer clearly and safely; if you are unsure, say so and suggest verifying "
    "with the owner's manual or a qualified mechanic."
)


@router.post("/ai/generate", response_model=GenerateResponse)
def generate(body: GenerateRequest):
    """
    Lab 5 blocking endpoint: prompt (optional if images) -> Gemini or OpenRouter -> JSON + cost log.
    """
    try:
        result = llm_service.generate(
            prompt=body.prompt,
            system=body.system or _DEFAULT_SYSTEM,
            model=body.model,
            purpose="api_generate",
            images=body.images,
        )
        return GenerateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
