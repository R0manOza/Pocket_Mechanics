"""
Lab 6 — SSE streaming chat with session memory.
POST /api/ai/stream — text/event-stream, data: {"token":"..."}, then usage, then [DONE].
"""

import json
import os
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

from services import llm_service, vision_utils
from services.episode_logger import log_error, log_stream_end, log_user_message
from services.session_service import load_session, save_session

router = APIRouter()

_DEFAULT_SYSTEM = (
    "You are Pocket Mechanics, a beginner-friendly car maintenance assistant. "
    "Be concise unless the user asks for detail. If unsure, say so."
)


class StreamRequest(BaseModel):
    message: str = Field(default="", max_length=50000)
    session_id: str = Field(..., min_length=1)
    images: list[str] | None = Field(
        default=None,
        description="data:image/jpeg|png|gif|webp;base64,... (see MAX_VISION_* in .env)",
    )
    system: str | None = None
    model: str | None = None

    @model_validator(mode="after")
    def message_or_images(self):
        has_text = bool(self.message.strip())
        has_images = bool(self.images and len(self.images) > 0)
        if not has_text and not has_images:
            raise ValueError("Provide a non-empty message and/or at least one image.")
        if self.images is not None and len(self.images) == 0:
            raise ValueError("If images is set, include at least one data URL.")
        return self


def _gemini_history(non_system_messages: list) -> tuple[list, str | list]:
    """Split into Gemini start_chat history and final user parts (text or multimodal list)."""
    if not non_system_messages:
        return [], ""
    if non_system_messages[-1]["role"] != "user":
        return [], ""
    last_content = non_system_messages[-1]["content"]
    prior = non_system_messages[:-1]
    hist: list = []
    i = 0
    while i < len(prior):
        if prior[i]["role"] != "user":
            i += 1
            continue
        parts = vision_utils.gemini_parts_from_openai_user_content(prior[i]["content"])
        hist.append({"role": "user", "parts": parts})
        if i + 1 < len(prior) and prior[i + 1]["role"] in ("assistant", "model"):
            hist.append({"role": "model", "parts": [prior[i + 1]["content"]]})
            i += 2
        else:
            i += 1
    last_parts = vision_utils.gemini_parts_from_openai_user_content(last_content)
    return hist, last_parts


async def _token_generator(session_id: str, messages: list, model_override: str | None):
    stream_start_ms = int(time.time() * 1000)
    full_response = ""
    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0

    routing = llm_service.get_routing()
    model_used = (
        llm_service.normalize_openrouter_model(model_override)
        if routing == "openrouter"
        else llm_service.normalize_gemini_model(model_override)
    )

    try:
        if routing == "openrouter":
            client = llm_service.get_openrouter_client()
            response = client.chat.completions.create(
                model=model_used,
                messages=[
                    {
                        **message,
                        "content": llm_service._openrouter_system_content(message["content"], model_used)
                        if message.get("role") == "system" and isinstance(message.get("content"), str)
                        else message.get("content"),
                    }
                    for message in messages
                ],
                stream=True,
                stream_options={"include_usage": True},
            )
            for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        full_response += delta
                        yield f"data: {json.dumps({'token': delta})}\n\n"
                if chunk.usage:
                    input_tokens = chunk.usage.prompt_tokens or 0
                    output_tokens = chunk.usage.completion_tokens or 0
                    cache_read_tokens, cache_write_tokens = llm_service._cache_usage_from_openrouter(chunk.usage)

        else:
            llm_service.ensure_gemini()
            import google.generativeai as genai

            system = next(
                (m["content"] for m in messages if m.get("role") == "system"),
                _DEFAULT_SYSTEM,
            )
            non_sys = [m for m in messages if m.get("role") != "system"]
            gmodel = genai.GenerativeModel(model_used, system_instruction=system)
            hist, last_user_parts = _gemini_history(non_sys)

            if not hist:
                stream_iter = gmodel.generate_content(
                    last_user_parts,
                    stream=True,
                    request_options={"timeout": float(os.environ.get("GEMINI_TIMEOUT_SECONDS", "30"))},
                )
            else:
                chat = gmodel.start_chat(history=hist)
                stream_iter = chat.send_message(
                    last_user_parts,
                    stream=True,
                    request_options={"timeout": float(os.environ.get("GEMINI_TIMEOUT_SECONDS", "30"))},
                )

            for chunk in stream_iter:
                t = getattr(chunk, "text", None) or ""
                if t:
                    full_response += t
                    yield f"data: {json.dumps({'token': t})}\n\n"
                um = getattr(chunk, "usage_metadata", None)
                if um is not None:
                    input_tokens = getattr(um, "prompt_token_count", None) or input_tokens
                    output_tokens = getattr(um, "candidates_token_count", None) or output_tokens
                    cache_read_tokens = getattr(um, "cached_content_token_count", None) or cache_read_tokens

    except Exception as e:
        log_error(session_id, e, context="stream_generation")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

    finally:
        stream_end_ms = int(time.time() * 1000)
        yield (
            "data: "
            + json.dumps(
                {
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "stream_start_ms": stream_start_ms,
                        "stream_end_ms": stream_end_ms,
                        "latency_ms": stream_end_ms - stream_start_ms,
                        "cache_read_tokens": cache_read_tokens,
                        "cache_write_tokens": cache_write_tokens,
                        "fallback_triggered": False,
                    }
                }
            )
            + "\n\n"
        )
        log_stream_end(
            session_id=session_id,
            model=model_used or "unknown",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            stream_start_ms=stream_start_ms,
            stream_end_ms=stream_end_ms,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            fallback_triggered=False,
        )
        if full_response:
            messages.append({"role": "assistant", "content": full_response})
            save_session(session_id, messages)
        yield "data: [DONE]\n\n"


@router.post("/ai/stream")
async def stream_chat(body: StreamRequest):
    try:
        validated_images = vision_utils.validate_image_data_urls(body.images)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    log_user_message(body.session_id)

    messages = load_session(body.session_id)
    system = body.system or _DEFAULT_SYSTEM
    if not messages:
        messages = [{"role": "system", "content": system}]
    user_content = vision_utils.openrouter_user_content(body.message, validated_images)
    messages.append({"role": "user", "content": user_content})
    # Persist user turn immediately so a failed stream does not lose the message.
    save_session(body.session_id, messages)

    model_override = body.model or os.environ.get("STREAM_MODEL")

    return StreamingResponse(
        _token_generator(body.session_id, messages, model_override),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
