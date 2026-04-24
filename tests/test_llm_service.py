"""
Integration tests for LLM service (routing, normalization, cost calculation).
"""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestLLMServiceRouting:
    """Test routing between Gemini and OpenRouter."""

    def test_routing_prefers_openrouter_when_both_keys_present(self, reset_llm_service):
        """Test that OpenRouter is preferred when both keys are set."""
        os.environ["GEMINI_API_KEY"] = "gemini-key"
        os.environ["OPENROUTER_KEY"] = "openrouter-key"
        os.environ["USE_DIRECT_GEMINI"] = "false"

        from services import llm_service

        assert llm_service.get_routing() == "openrouter"

    def test_routing_uses_gemini_when_use_direct_is_true(self, reset_llm_service):
        """Test that Gemini is used when USE_DIRECT_GEMINI=true."""
        os.environ["GEMINI_API_KEY"] = "gemini-key"
        os.environ["OPENROUTER_KEY"] = "openrouter-key"
        os.environ["USE_DIRECT_GEMINI"] = "true"

        from services import llm_service

        assert llm_service.get_routing() == "gemini"

    def test_routing_uses_gemini_alone(self, reset_llm_service):
        """Test that Gemini is used when only GEMINI_API_KEY is set."""
        os.environ["GEMINI_API_KEY"] = "gemini-key"
        if "OPENROUTER_KEY" in os.environ:
            del os.environ["OPENROUTER_KEY"]
        os.environ["USE_DIRECT_GEMINI"] = "false"

        from services import llm_service

        assert llm_service.get_routing() == "gemini"

    def test_routing_uses_openrouter_alone(self, reset_llm_service):
        """Test that OpenRouter is used when only OPENROUTER_KEY is set."""
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        os.environ["OPENROUTER_KEY"] = "openrouter-key"

        from services import llm_service

        assert llm_service.get_routing() == "openrouter"

    def test_routing_raises_when_no_keys(self, reset_llm_service):
        """Test that routing raises error when no API keys are set."""
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        if "OPENROUTER_KEY" in os.environ:
            del os.environ["OPENROUTER_KEY"]

        from services import llm_service

        with pytest.raises(RuntimeError):
            llm_service.get_routing()


class TestModelNormalization:
    """Test model name normalization."""

    def test_normalize_gemini_model_default(self, reset_llm_service):
        """Test default Gemini model normalization."""
        from services import llm_service

        result = llm_service.normalize_gemini_model(None)
        assert result == "gemini-2.5-flash"

    def test_normalize_gemini_model_strips_prefix(self, reset_llm_service):
        """Test that 'google/' prefix is stripped from Gemini models."""
        from services import llm_service

        result = llm_service.normalize_gemini_model("google/gemini-2.5-pro")
        assert result == "gemini-2.5-pro"

    def test_normalize_gemini_model_preserves_short_name(self, reset_llm_service):
        """Test that short model names are preserved."""
        from services import llm_service

        result = llm_service.normalize_gemini_model("gemini-2.5-pro")
        assert result == "gemini-2.5-pro"

    def test_normalize_gemini_model_strips_whitespace(self, reset_llm_service):
        """Test that whitespace is stripped."""
        from services import llm_service

        result = llm_service.normalize_gemini_model("  gemini-2.5-flash  ")
        assert result == "gemini-2.5-flash"

    def test_normalize_openrouter_model_default(self, reset_llm_service):
        """Test default OpenRouter model."""
        from services import llm_service

        result = llm_service.normalize_openrouter_model(None)
        assert result == "google/gemini-2.5-flash"

    def test_normalize_openrouter_model_strips_whitespace(self, reset_llm_service):
        """Test that OpenRouter model names strip whitespace."""
        from services import llm_service

        result = llm_service.normalize_openrouter_model("  openai/gpt-4o  ")
        assert result == "openai/gpt-4o"

    def test_normalize_openrouter_model_preserves_full_name(self, reset_llm_service):
        """Test that full OpenRouter model names are preserved."""
        from services import llm_service

        result = llm_service.normalize_openrouter_model("anthropic/claude-sonnet-4-6")
        assert result == "anthropic/claude-sonnet-4-6"


class TestCostCalculation:
    """Test cost calculation for different models."""

    def test_cost_free_model(self, reset_llm_service):
        """Test that free models have zero cost."""
        from services import llm_service

        cost = llm_service._calculate_cost("meta-llama/llama-4-maverick:free", 1000, 2000)
        assert cost == 0.0

    def test_cost_gemini_flash(self, reset_llm_service):
        """Test Gemini 2.5 Flash cost calculation."""
        from services import llm_service

        # Input: 0.15 per M, Output: 0.60 per M
        cost = llm_service._calculate_cost("google/gemini-2.5-flash", 1_000_000, 1_000_000)
        assert cost == pytest.approx(0.75, rel=0.01)  # 0.15 + 0.60

    def test_cost_claude_haiku(self, reset_llm_service):
        """Test Claude Haiku cost calculation."""
        from services import llm_service

        # Input: 1.00 per M, Output: 5.00 per M
        cost = llm_service._calculate_cost(
            "anthropic/claude-haiku-4-5-20251001", 1_000_000, 1_000_000
        )
        assert cost == pytest.approx(6.0, rel=0.01)

    def test_cost_unknown_model_defaults_to_zero(self, reset_llm_service):
        """Test that unknown models default to zero cost."""
        from services import llm_service

        cost = llm_service._calculate_cost("unknown/model", 1_000_000, 1_000_000)
        assert cost == 0.0

    def test_cost_partial_tokens(self, reset_llm_service):
        """Test cost calculation with partial tokens."""
        from services import llm_service

        # 500k input, 250k output at Flash rates
        cost = llm_service._calculate_cost("google/gemini-2.5-flash", 500_000, 250_000)
        expected = (500_000 / 1_000_000) * 0.15 + (250_000 / 1_000_000) * 0.60
        assert cost == pytest.approx(expected, rel=0.01)


class TestOpenRouterClient:
    """Test OpenRouter client initialization."""

    def test_get_openrouter_client_singleton(self, reset_llm_service):
        """Test that OpenRouter client is a singleton."""
        from services import llm_service

        client1 = llm_service.get_openrouter_client()
        client2 = llm_service.get_openrouter_client()
        assert client1 is client2

    def test_get_openrouter_client_raises_without_key(self, reset_llm_service):
        """Test that getting OpenRouter client fails without key."""
        if "OPENROUTER_KEY" in os.environ:
            del os.environ["OPENROUTER_KEY"]
        os.environ["GEMINI_API_KEY"] = "gemini-key"

        from services import llm_service

        with pytest.raises(RuntimeError):
            llm_service.get_openrouter_client()


class TestGenerateBlocking:
    """Test blocking generate function."""

    def test_generate_with_openrouter(self, reset_llm_service, temp_logs_dir):
        """Test blocking generate with OpenRouter."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Generated text"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 250
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            import llm_service

            result = llm_service.generate(
                prompt="Test prompt",
                system="Test system",
                model=None,
                purpose="test_purpose",
            )

            assert result["content"] == "Generated text"
            assert result["input_tokens"] == 100
            assert result["output_tokens"] == 250
            assert result["latency_ms"] > 0
            assert result["cost_usd"] >= 0

    def test_generate_with_gemini(self, reset_llm_service, temp_logs_dir):
        """Test blocking generate with Gemini."""
        os.environ["USE_DIRECT_GEMINI"] = "true"
        os.environ["OPENROUTER_KEY"] = ""

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini response"
        mock_usage = MagicMock()
        mock_usage.prompt_token_count = 50
        mock_usage.candidates_token_count = 150
        mock_response.usage_metadata = mock_usage
        mock_model.generate_content.return_value = mock_response

        with patch("services.llm_service._ensure_genai"):
            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                import llm_service

                result = llm_service.generate(
                    prompt="Test",
                    system="System",
                    model=None,
                    purpose="test",
                )

                assert result["content"] == "Gemini response"
                assert result["input_tokens"] == 50
                assert result["output_tokens"] == 150

    def test_generate_logs_to_cost_file(self, reset_llm_service, temp_logs_dir):
        """Test that generate logs to cost log file."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Text"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            import llm_service

            llm_service.generate(
                prompt="Test",
                system="System",
                purpose="test_log",
            )

            # Check log file was created
            assert os.path.exists(os.environ["COST_LOG_PATH"])

    def test_generate_with_custom_model(self, reset_llm_service, temp_logs_dir):
        """Test generate with custom model override."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 5
        mock_usage.completion_tokens = 15
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        with patch("services.llm_service._get_openrouter_client", return_value=mock_client):
            import llm_service

            llm_service.generate(
                prompt="Test",
                model="anthropic/claude-sonnet-4-6",
            )

            # Verify correct model was used
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "anthropic/claude-sonnet-4-6"
