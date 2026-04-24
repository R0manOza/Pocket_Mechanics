"""
Shared pytest fixtures and configuration for integration tests.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add Backend to path FIRST before any other imports
backend_path = Path(__file__).resolve().parents[1] / "Backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Make old test imports like `import llm_service` point to the real module:
# Backend/services/llm_service.py
from services import llm_service as _llm_service
sys.modules["llm_service"] = _llm_service

from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def setup_env():
    """Set up test environment with mock .env variables."""
    test_env = {
        "GEMINI_API_KEY": "test-gemini-key",
        "OPENROUTER_KEY": "test-openrouter-key",
        "DEFAULT_MODEL": "google/gemini-2.5-flash",
        "GEMINI_MODEL": "gemini-2.5-flash",
        "USE_DIRECT_GEMINI": "false",
        "EPISODE_LOG_PATH": None,
        "COST_LOG_PATH": None,
    }
    for key, value in test_env.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]
    yield
    # Cleanup
    for key in test_env:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def temp_logs_dir(tmp_path):
    """Provide temporary directory for logs."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    os.environ["COST_LOG_PATH"] = str(log_dir / "cost-log.csv")
    os.environ["EPISODE_LOG_PATH"] = str(log_dir / "episode-log.csv")
    yield log_dir
    # Cleanup
    for key in ["COST_LOG_PATH", "EPISODE_LOG_PATH"]:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def reset_llm_service():
    """Reset global state in llm_service between tests."""
    import importlib
    import sys

    backend_path = Path(__file__).resolve().parents[1] / "Backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))

    from services import llm_service

    reloaded = importlib.reload(llm_service)
    sys.modules["llm_service"] = reloaded

    yield

    reloaded = importlib.reload(llm_service)
    sys.modules["llm_service"] = reloaded

@pytest.fixture
def reset_session_service():
    """Reset global session state between tests."""
    import importlib
    import sys

    # Ensure path is set
    backend_path = Path(__file__).resolve().parents[1] / "Backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))

    from services import session_service

    importlib.reload(session_service)
    yield
    importlib.reload(session_service)


@pytest.fixture
def mock_gemini_client():
    """Mock Google Generative AI client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Test response from Gemini"
    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 10
    mock_usage.candidates_token_count = 25
    mock_response.usage_metadata = mock_usage
    mock_client.generate_content.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_openrouter_client():
    """Mock OpenRouter (OpenAI-compatible) client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Test response from OpenRouter"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 15
    mock_usage.completion_tokens = 30
    mock_response.usage = mock_usage
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_gemini_stream():
    """Mock streaming response from Gemini."""
    mock_chunk_1 = MagicMock()
    mock_chunk_1.text = "Hello "
    mock_um_1 = MagicMock()
    mock_um_1.prompt_token_count = 10
    mock_um_1.candidates_token_count = 0
    mock_chunk_1.usage_metadata = mock_um_1

    mock_chunk_2 = MagicMock()
    mock_chunk_2.text = "from Gemini"
    mock_um_2 = MagicMock()
    mock_um_2.prompt_token_count = None
    mock_um_2.candidates_token_count = 5
    mock_chunk_2.usage_metadata = mock_um_2

    mock_chunk_3 = MagicMock()
    mock_chunk_3.text = "!"
    mock_um_3 = MagicMock()
    mock_um_3.prompt_token_count = None
    mock_um_3.candidates_token_count = 20
    mock_chunk_3.usage_metadata = mock_um_3

    return [mock_chunk_1, mock_chunk_2, mock_chunk_3]


@pytest.fixture
def mock_openrouter_stream():
    """Mock streaming response from OpenRouter."""
    chunks = []
    for text in ["Hello ", "from ", "OpenRouter", "!"]:
        chunk = MagicMock()
        choice = MagicMock()
        delta = MagicMock()
        delta.content = text
        choice.delta = delta
        chunk.choices = [choice]
        chunk.usage = None
        chunks.append(chunk)

    # Final chunk with usage
    final_chunk = MagicMock()
    final_choice = MagicMock()
    final_delta = MagicMock()
    final_delta.content = None
    final_choice.delta = final_delta
    final_chunk.choices = [final_choice]
    final_usage = MagicMock()
    final_usage.prompt_tokens = 12
    final_usage.completion_tokens = 25
    final_chunk.usage = final_usage
    chunks.append(final_chunk)

    return chunks


@pytest.fixture
def test_client():
    """Create a FastAPI TestClient."""
    # Import fresh app for testing
    from main import app

    return TestClient(app)


@pytest.fixture
def app_with_mocks(mock_openrouter_client, reset_llm_service, reset_session_service, temp_logs_dir):
    """Create app with mocked LLM services."""
    with patch("services.llm_service._get_openrouter_client", return_value=mock_openrouter_client):
        from main import app

        yield TestClient(app)
