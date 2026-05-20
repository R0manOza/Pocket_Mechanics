from pydantic import BaseModel, Field, model_validator


class GenerateRequest(BaseModel):
    prompt: str = Field(
        default="",
        max_length=50000,
        description="User question; optional if `images` is non-empty",
    )
    images: list[str] | None = Field(
        None,
        description=(
            "Optional vision input: data URLs from your camera roll "
            "(`data:image/jpeg|png|gif|webp|heic;base64,...`)"
        ),
    )
    system: str | None = Field(
        None,
        description="Optional system prompt; defaults to a car-maintenance assistant",
    )
    model: str | None = Field(
        None,
        description="Optional model id — OpenRouter slug or Gemini short name; see .env",
    )

    @model_validator(mode="after")
    def require_prompt_or_images(self):
        has_text = bool(self.prompt.strip())
        has_images = bool(self.images and len(self.images) > 0)
        if not has_text and not has_images:
            raise ValueError("Provide a non-empty prompt and/or at least one image.")
        if self.images is not None and len(self.images) == 0:
            raise ValueError("If `images` is set, include at least one data URL.")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt": "What part is circled here and is it safe to drive?",
                "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRg..."],
                "system": "You explain car parts in simple language for non-mechanics.",
            }
        }
    }


class GenerateResponse(BaseModel):
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    latency_ms: int
    fallback_triggered: bool = False
    cost_usd: float
