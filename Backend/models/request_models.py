from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        description="User question (text-only for Lab 5)",
    )
    system: str | None = Field(
        None,
        description="Optional system prompt; defaults to a car-maintenance assistant",
    )
    model: str | None = Field(
        None,
        description="Optional OpenRouter model id — defaults to DEFAULT_MODEL in .env",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt": "What is a serpentine belt and what are signs it needs replacing?",
                "system": "You explain car parts in simple language for non-mechanics.",
            }
        }
    }


class GenerateResponse(BaseModel):
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_usd: float