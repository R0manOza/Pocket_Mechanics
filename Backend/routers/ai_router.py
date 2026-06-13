from fastapi import APIRouter, Depends, HTTPException
from models.request_models import GenerateRequest, GenerateResponse
from services import llm_service
from services.rate_limit import rate_limit

router = APIRouter()

@router.post(
    "/ai/generate",
    response_model=GenerateResponse,
    dependencies=[Depends(rate_limit)],
)
def generate(body: GenerateRequest):
    """
    Lab 5 blocking endpoint: prompt (optional if images) -> Gemini or OpenRouter -> JSON + cost log.
    """
    try:
        result = llm_service.generate(
            prompt=body.prompt,
            system=llm_service.build_system_prompt(body.system),
            model=body.model,
            purpose="api_generate",
            images=body.images,
        )
        return GenerateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
