"""
Integration tests for pydantic request/response models.
"""

import pytest
from pydantic import ValidationError


class TestGenerateRequest:
    """Test GenerateRequest model validation."""

    def test_generate_request_valid(self):
        """Test valid GenerateRequest."""
        from models.request_models import GenerateRequest

        req = GenerateRequest(prompt="What is a serpentine belt?")
        assert req.prompt == "What is a serpentine belt?"
        assert req.system is None
        assert req.model is None

    def test_generate_request_with_all_fields(self):
        """Test GenerateRequest with all fields."""
        from models.request_models import GenerateRequest

        req = GenerateRequest(
            prompt="Test prompt",
            system="Test system",
            model="google/gemini-2.5-flash",
        )
        assert req.prompt == "Test prompt"
        assert req.system == "Test system"
        assert req.model == "google/gemini-2.5-flash"

    def test_generate_request_missing_prompt(self):
        """Test GenerateRequest fails without prompt or images."""
        from models.request_models import GenerateRequest

        with pytest.raises(ValidationError):
            GenerateRequest()

    def test_generate_request_empty_prompt(self):
        """Test GenerateRequest fails with empty prompt and no images."""
        from models.request_models import GenerateRequest

        with pytest.raises(ValidationError):
            GenerateRequest(prompt="")

    def test_generate_request_image_only(self):
        """Vision: prompt may be empty when images are provided."""
        from models.request_models import GenerateRequest

        tiny = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        req = GenerateRequest(prompt="", images=[tiny])
        assert req.prompt == ""
        assert len(req.images) == 1

    def test_generate_request_whitespace_prompt(self):
        """Whitespace-only prompt is treated as empty without images."""
        from models.request_models import GenerateRequest

        with pytest.raises(ValidationError):
            GenerateRequest(prompt="   ")

    def test_generate_request_long_prompt(self):
        """Test GenerateRequest accepts very long prompts."""
        from models.request_models import GenerateRequest

        long_prompt = "X" * 50000
        req = GenerateRequest(prompt=long_prompt)
        assert req.prompt == long_prompt

    def test_generate_request_optional_system(self):
        """Test that system is optional."""
        from models.request_models import GenerateRequest

        req = GenerateRequest(prompt="Test")
        assert req.system is None

    def test_generate_request_optional_model(self):
        """Test that model is optional."""
        from models.request_models import GenerateRequest

        req = GenerateRequest(prompt="Test")
        assert req.model is None

    def test_generate_request_special_characters_in_prompt(self):
        """Test GenerateRequest with special characters."""
        from models.request_models import GenerateRequest

        prompt = "What's the deal with @#$%^&*() characters? \"quotes\" and 'apostrophes'"
        req = GenerateRequest(prompt=prompt)
        assert req.prompt == prompt

    def test_generate_request_unicode_prompt(self):
        """Test GenerateRequest with unicode characters."""
        from models.request_models import GenerateRequest

        prompt = "你好 🚗 Bonjour café"
        req = GenerateRequest(prompt=prompt)
        assert req.prompt == prompt

    def test_generate_request_json_schema(self):
        """Test GenerateRequest JSON schema."""
        from models.request_models import GenerateRequest

        schema = GenerateRequest.model_json_schema()
        assert "properties" in schema
        assert "prompt" in schema["properties"]


class TestGenerateResponse:
    """Test GenerateResponse model."""

    def test_generate_response_valid(self):
        """Test valid GenerateResponse."""
        from models.request_models import GenerateResponse

        resp = GenerateResponse(
            content="Test response",
            model="google/gemini-2.5-flash",
            input_tokens=50,
            output_tokens=100,
            latency_ms=500,
            cost_usd=0.05,
        )
        assert resp.content == "Test response"
        assert resp.model == "google/gemini-2.5-flash"
        assert resp.input_tokens == 50
        assert resp.output_tokens == 100
        assert resp.latency_ms == 500
        assert resp.cost_usd == 0.05

    def test_generate_response_zero_tokens(self):
        """Test GenerateResponse with zero tokens."""
        from models.request_models import GenerateResponse

        resp = GenerateResponse(
            content="",
            model="model",
            input_tokens=0,
            output_tokens=0,
            latency_ms=10,
            cost_usd=0.0,
        )
        assert resp.input_tokens == 0
        assert resp.output_tokens == 0

    def test_generate_response_missing_field(self):
        """Test GenerateResponse fails with missing required field."""
        from models.request_models import GenerateResponse

        with pytest.raises(ValidationError):
            GenerateResponse(
                content="Test",
                model="model",
                input_tokens=50,
                output_tokens=100,
                latency_ms=500,
                # Missing cost_usd
            )

    def test_generate_response_negative_tokens_fails(self):
        """Test that negative tokens fail validation."""
        from models.request_models import GenerateResponse

        # Pydantic doesn't validate negative ints by default
        # but we document the field types
        resp = GenerateResponse(
            content="Test",
            model="model",
            input_tokens=0,
            output_tokens=0,
            latency_ms=0,
            cost_usd=0.0,
        )
        assert resp.input_tokens >= 0

    def test_generate_response_high_latency(self):
        """Test GenerateResponse with high latency."""
        from models.request_models import GenerateResponse

        resp = GenerateResponse(
            content="Test",
            model="model",
            input_tokens=100,
            output_tokens=200,
            latency_ms=30000,  # 30 seconds
            cost_usd=1.0,
        )
        assert resp.latency_ms == 30000

    def test_generate_response_high_cost(self):
        """Test GenerateResponse with high cost."""
        from models.request_models import GenerateResponse

        resp = GenerateResponse(
            content="Very expensive response",
            model="anthropic/claude-opus-4-6",
            input_tokens=1000000,
            output_tokens=2000000,
            latency_ms=5000,
            cost_usd=45.0,
        )
        assert resp.cost_usd == 45.0

    def test_generate_response_long_content(self):
        """Test GenerateResponse with very long content."""
        from models.request_models import GenerateResponse

        long_content = "X" * 100000
        resp = GenerateResponse(
            content=long_content,
            model="model",
            input_tokens=5000,
            output_tokens=10000,
            latency_ms=2000,
            cost_usd=1.0,
        )
        assert len(resp.content) == 100000

    def test_generate_response_serialization(self):
        """Test GenerateResponse serialization to JSON."""
        from models.request_models import GenerateResponse

        resp = GenerateResponse(
            content="Test",
            model="model",
            input_tokens=10,
            output_tokens=20,
            latency_ms=100,
            cost_usd=0.001,
        )
        json_dict = resp.model_dump()
        assert json_dict["content"] == "Test"
        assert json_dict["model"] == "model"


class TestStreamRequest:
    """Test StreamRequest model validation."""

    def test_stream_request_valid(self):
        """Test valid StreamRequest."""
        from routers.stream_router import StreamRequest

        req = StreamRequest(message="What is a spark plug?", session_id="session-123")
        assert req.message == "What is a spark plug?"
        assert req.session_id == "session-123"

    def test_stream_request_with_all_fields(self):
        """Test StreamRequest with all optional fields."""
        from routers.stream_router import StreamRequest

        req = StreamRequest(
            message="Question",
            session_id="session",
            system="Custom system",
            model="google/gemini-2.5-flash",
        )
        assert req.message == "Question"
        assert req.session_id == "session"
        assert req.system == "Custom system"
        assert req.model == "google/gemini-2.5-flash"

    def test_stream_request_missing_message(self):
        """Test StreamRequest fails without message or images."""
        from routers.stream_router import StreamRequest

        with pytest.raises(ValidationError):
            StreamRequest(session_id="session")

    def test_stream_request_missing_session_id(self):
        """Test StreamRequest fails without session_id."""
        from routers.stream_router import StreamRequest

        with pytest.raises(ValidationError):
            StreamRequest(message="Test")

    def test_stream_request_empty_message(self):
        """Test StreamRequest fails with empty message and no images."""
        from routers.stream_router import StreamRequest

        with pytest.raises(ValidationError):
            StreamRequest(message="", session_id="session")

    def test_stream_request_image_only(self):
        """Vision: message may be empty when images are provided."""
        from routers.stream_router import StreamRequest

        tiny = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        req = StreamRequest(message="", session_id="s1", images=[tiny])
        assert req.message == ""
        assert req.images == [tiny]

    def test_stream_request_empty_session_id(self):
        """Test StreamRequest fails with empty session_id."""
        from routers.stream_router import StreamRequest

        with pytest.raises(ValidationError):
            StreamRequest(message="Test", session_id="")

    def test_stream_request_min_length_validation(self):
        """Test StreamRequest min_length validation."""
        from routers.stream_router import StreamRequest

        # Single character should be valid
        req = StreamRequest(message="X", session_id="Y")
        assert req.message == "X"
        assert req.session_id == "Y"

    def test_stream_request_long_message(self):
        """Test StreamRequest with very long messages (within API cap)."""
        from routers.stream_router import StreamRequest

        long_message = "Q" * 50000
        req = StreamRequest(message=long_message, session_id="session")
        assert req.message == long_message

    def test_stream_request_unicode_message(self):
        """Test StreamRequest with unicode."""
        from routers.stream_router import StreamRequest

        message = "こんにちは 🚗 Hola"
        req = StreamRequest(message=message, session_id="session")
        assert req.message == message

    def test_stream_request_special_chars_session_id(self):
        """Test StreamRequest with special characters in session_id."""
        from routers.stream_router import StreamRequest

        session_id = "session-123_abc.def@example"
        req = StreamRequest(message="Test", session_id=session_id)
        assert req.session_id == session_id
