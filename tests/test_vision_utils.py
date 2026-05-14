"""Unit tests for vision / multimodal helpers."""

import pytest

from services import vision_utils

TINY_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_validate_image_data_urls_accepts_png():
    assert vision_utils.validate_image_data_urls([TINY_PNG]) == [TINY_PNG]


def test_validate_image_data_urls_rejects_plain_string():
    with pytest.raises(ValueError):
        vision_utils.validate_image_data_urls(["https://example.com/x.png"])


def test_openrouter_user_content_with_text_and_image():
    parts = vision_utils.openrouter_user_content("Hello", [TINY_PNG])
    assert isinstance(parts, list)
    assert parts[0] == {"type": "text", "text": "Hello"}
    assert parts[1]["type"] == "image_url"
    assert parts[1]["image_url"]["url"] == TINY_PNG


def test_openrouter_user_content_text_only():
    assert vision_utils.openrouter_user_content("Hi", []) == "Hi"


def test_jpg_declared_mime_normalized_to_jpeg():
    """Some clients emit image/jpg; we normalize for APIs that expect image/jpeg."""
    b64 = TINY_PNG.split(",", 1)[1]
    url = f"data:image/jpg;base64,{b64}"
    mime, _ = vision_utils.parse_one_data_url(url)
    assert mime == "image/jpeg"


def test_gemini_parts_from_openai_round_trip():
    openai_user = [
        {"type": "text", "text": "Look"},
        {"type": "image_url", "image_url": {"url": TINY_PNG}},
    ]
    gem = vision_utils.gemini_parts_from_openai_user_content(openai_user)
    assert isinstance(gem, list)
    assert gem[0] == "Look"
    assert "inline_data" in gem[1]
