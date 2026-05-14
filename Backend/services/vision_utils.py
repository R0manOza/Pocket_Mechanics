"""
Validate vision payloads (data URLs) and build multimodal user content for Gemini / OpenRouter.

Env (budget / abuse limits):
  MAX_VISION_IMAGES — max images per request (default 2)
  MAX_VISION_BYTES_PER_IMAGE — decoded bytes per image (default 5 MB)
"""

from __future__ import annotations

import base64
import binascii
import os
import re
from typing import Any

_ALLOWED_MIME = frozenset(
    {"image/jpeg", "image/png", "image/gif", "image/webp", "image/heic", "image/heif"}
)

# Browsers emit data:image/jpeg;base64,... (case varies). Allow jpg/heic/heif from phones.
_DATA_URL_RE = re.compile(
    r"^data:(image/(?:jpeg|jpg|png|gif|webp|heic|heif));base64,([A-Za-z0-9+/=\r\n]+)\s*$",
    re.IGNORECASE | re.DOTALL,
)


def max_vision_images() -> int:
    return max(1, int(os.environ.get("MAX_VISION_IMAGES", "2")))


def max_vision_bytes_per_image() -> int:
    # Default 5 MB to match Frontend ImageUploader cap.
    return max(1024, int(os.environ.get("MAX_VISION_BYTES_PER_IMAGE", str(5 * 1024 * 1024))))


def parse_one_data_url(data_url: str) -> tuple[str, str]:
    """
    Return (mime_type_lowercase, base64_payload_without_whitespace) for inline APIs.
    """
    m = _DATA_URL_RE.match(data_url.strip())
    if not m:
        raise ValueError(
            "Each image must be a data URL from your device: "
            "data:image/jpeg|jpg|png|gif|webp|heic|heif;base64,..."
        )
    mime = m.group(1).lower()
    if mime == "image/jpg":
        mime = "image/jpeg"
    if mime not in _ALLOWED_MIME:
        raise ValueError(f"Unsupported image type: {mime}")
    b64 = re.sub(r"\s+", "", m.group(2))
    try:
        raw = base64.b64decode(b64, validate=True)
    except binascii.Error as e:
        raise ValueError("Invalid base64 in image data URL") from e
    lim = max_vision_bytes_per_image()
    if len(raw) > lim:
        raise ValueError(f"Image too large after decode (max {lim} bytes)")
    return mime, b64


def validate_image_data_urls(urls: list[str] | None) -> list[str]:
    """Return normalized data URL strings (same as input if valid)."""
    if not urls:
        return []
    if len(urls) > max_vision_images():
        raise ValueError(f"Too many images (max {max_vision_images()})")
    out: list[str] = []
    for u in urls:
        parse_one_data_url(u)
        out.append(u.strip())
    return out


def openrouter_user_content(text: str, image_data_urls: list[str]) -> str | list[dict[str, Any]]:
    """OpenAI-compatible user message `content` (string or multimodal parts)."""
    if not image_data_urls:
        return text

    parts: list[dict[str, Any]] = []
    if text.strip():
        parts.append({"type": "text", "text": text.strip()})
    else:
        parts.append(
            {
                "type": "text",
                "text": (
                    "You are helping with a car maintenance / parts question. "
                    "Describe what you see in the image(s) and give practical, "
                    "safety-conscious guidance."
                ),
            }
        )
    for url in image_data_urls:
        parts.append({"type": "image_url", "image_url": {"url": url}})
    return parts


def gemini_generate_parts(text: str, image_data_urls: list[str]) -> list[Any]:
    """Parts list for GenerativeModel.generate_content (text + inline images)."""
    parts: list[Any] = []
    if text.strip():
        parts.append(text.strip())
    else:
        parts.append(
            "You are helping with a car maintenance / parts question. "
            "Describe what you see in the image(s) and give practical, safety-conscious guidance."
        )
    for url in image_data_urls:
        mime, b64 = parse_one_data_url(url)
        parts.append({"inline_data": {"mime_type": mime, "data": b64}})
    return parts


def gemini_parts_from_openai_user_content(content: str | list[Any]) -> list[Any]:
    """
    Convert stored session user `content` (OpenAI-style string or multimodal list)
    into Gemini `parts` for start_chat history or send_message.
    """
    if isinstance(content, str):
        return [content]

    parts: list[Any] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            t = block.get("text")
            if isinstance(t, str) and t:
                parts.append(t)
        elif block.get("type") == "image_url":
            url_obj = block.get("image_url")
            url = url_obj.get("url") if isinstance(url_obj, dict) else None
            if isinstance(url, str) and url.startswith("data:"):
                mime, b64 = parse_one_data_url(url)
                parts.append({"inline_data": {"mime_type": mime, "data": b64}})
    return parts if parts else ["."]
