"""
Integration tests for AI router (generate endpoint).
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from routers import ai_router


class TestGenerateEndpoint:
    """Test /api/ai/generate endpoint with blocking LLM calls."""

    def test_generate_with_valid_request_openrouter(self, app_with_mocks, mock_openrouter_client):
        """Test successful text generation via OpenRouter."""
        response = app_with_mocks.post(
            "/api/ai/generate",
            json={
                "prompt": "What is a serpentine belt?",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test response from OpenRouter"
        assert data["model"] == "google/gemini-2.5-flash"
        assert data["input_tokens"] == 15
        assert data["output_tokens"] == 30
        assert data["latency_ms"] > 0
        assert data["cost_usd"] >= 0

    def test_generate_with_custom_system_prompt(self, app_with_mocks, mock_openrouter_client):
        """Test generate with custom system prompt."""
        custom_system = "You are a mechanic. Be technical."
        response = app_with_mocks.post(
            "/api/ai/generate",
            json={
                "prompt": "Explain transmission fluid change",
                "system": custom_system,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["model"] == "google/gemini-2.5-flash"
        # Verify the custom system was passed to OpenRouter
        mock_openrouter_client.chat.completions.create.assert_called()
        call_args = mock_openrouter_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == custom_system

    def test_generate_with_custom_model(self, reset_llm_service, reset_session_service, temp_logs_dir):
        """Test generate with custom model override."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Custom model response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 20
        mock_usage.completion_tokens = 15
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.post(
                "/api/ai/generate",
                json={
                    "prompt": "Test prompt",
                    "model": "anthropic/claude-haiku-4-5-20251001",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["model"] == "anthropic/claude-haiku-4-5-20251001"

    def test_generate_with_empty_prompt(self, app_with_mocks):
        """Test generate with empty prompt fails validation."""
        response = app_with_mocks.post(
            "/api/ai/generate",
            json={
                "prompt": "",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_generate_with_missing_prompt(self, app_with_mocks):
        """Test generate with missing prompt."""
        response = app_with_mocks.post(
            "/api/ai/generate",
            json={},
        )

        assert response.status_code == 422  # Validation error

    def test_generate_default_system_prompt(self, app_with_mocks, mock_openrouter_client):
        """Test that default system prompt is used when not provided."""
        response = app_with_mocks.post(
            "/api/ai/generate",
            json={
                "prompt": "Question?",
            },
        )

        assert response.status_code == 200
        call_args = mock_openrouter_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        system_msg = messages[0]["content"]
        assert "Pocket Mechanics" in system_msg

    def test_generate_cost_calculation_free_model(self, reset_llm_service, reset_session_service, temp_logs_dir):
        """Test cost calculation for free models (should be 0)."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Free response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 1000
        mock_usage.completion_tokens = 5000
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.post(
                "/api/ai/generate",
                json={
                    "prompt": "Test",
                    "model": "meta-llama/llama-4-maverick:free",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["cost_usd"] == 0.0

    def test_generate_response_model_validation(self, app_with_mocks):
        """Test that response matches GenerateResponse schema."""
        response = app_with_mocks.post(
            "/api/ai/generate",
            json={"prompt": "Test"},
        )

        assert response.status_code == 200
        data = response.json()
        required_fields = ["content", "model", "input_tokens", "output_tokens", "latency_ms", "cost_usd"]
        for field in required_fields:
            assert field in data
        assert isinstance(data["content"], str)
        assert isinstance(data["model"], str)
        assert isinstance(data["input_tokens"], int)
        assert isinstance(data["output_tokens"], int)
        assert isinstance(data["latency_ms"], int)
        assert isinstance(data["cost_usd"], float)

    def test_generate_error_handling(self, reset_llm_service, reset_session_service, temp_logs_dir):
        """Test error handling when LLM service fails."""
        with patch("services.llm_service._get_openrouter_client") as mock_get_client:
            mock_get_client.side_effect = RuntimeError("API connection failed")

            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.post(
                "/api/ai/generate",
                json={"prompt": "Test"},
            )

            assert response.status_code == 500
            assert "detail" in response.json()

    def test_generate_with_long_prompt(self, app_with_mocks, mock_openrouter_client):
        """Test generate with very long prompt."""
        long_prompt = "Question? " * 500  # Very long prompt
        response = app_with_mocks.post(
            "/api/ai/generate",
            json={"prompt": long_prompt},
        )

        assert response.status_code == 200
        call_args = mock_openrouter_client.chat.completions.create.call_args
        sent_prompt = call_args[1]["messages"][-1]["content"]
        assert sent_prompt == long_prompt

    def test_generate_request_model_fields(self, app_with_mocks):
        """Test that GenerateRequest accepts all expected fields."""
        response = app_with_mocks.post(
            "/api/ai/generate",
            json={
                "prompt": "What are spark plugs?",
                "system": "Custom system",
                "model": "google/gemini-2.5-flash",
            },
        )

        assert response.status_code == 200

    def test_generate_response_includes_model_name(self, reset_llm_service, reset_session_service, temp_logs_dir):
        """Test that response includes the actual model name used."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            from main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.post(
                "/api/ai/generate",
                json={"prompt": "Test", "model": "openai/gpt-4o"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["model"] == "openai/gpt-4o"
