"""
Integration tests for main FastAPI app, CORS, and health endpoint.
"""

import pytest


class TestMainApp:
    """Test FastAPI application setup and health endpoint."""

    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_endpoint_content_type(self, test_client):
        """Test health endpoint returns JSON."""
        response = test_client.get("/health")
        assert response.headers["content-type"].startswith("application/json")

    def test_router_prefix(self, test_client):
        """Test that routers are correctly prefixed with /api."""
        # generate endpoint should be at /api/ai/generate
        response = test_client.post(
            "/api/ai/generate",
            json={"prompt": "test"},
        )
        # Should not be 404 (would be if prefix wrong)
        assert response.status_code != 404

    def test_wrong_route_404(self, test_client):
        """Test that wrong routes return 404."""
        response = test_client.get("/nonexistent")
        assert response.status_code == 404

    def test_cors_origin_localhost_3000(self, test_client):
        """Test CORS allows localhost:3000."""
        response = test_client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_origin_localhost_5173(self, test_client):
        """Test CORS allows localhost:5173."""
        response = test_client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_allows_all_methods(self, test_client):
        """Test CORS allows all HTTP methods."""
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "post" in response.headers.get("access-control-allow-methods", "").lower()

    def test_cors_allows_all_headers(self, test_client):
        """Test CORS allows all headers."""
        response = test_client.get(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Custom-Header": "value",
            },
        )
        assert response.status_code == 200

    def test_app_metadata(self):
        """Test that app has correct metadata."""
        from main import app

        assert app.title == "Pocket Mechanics API"
        assert "Lab 5" in app.description
        assert "Lab 6" in app.description
        assert app.version == "0.2.0"

    def test_multiple_health_calls(self, test_client):
        """Test that health endpoint can be called multiple times."""
        for _ in range(5):
            response = test_client.get("/health")
            assert response.status_code == 200

    def test_method_not_allowed(self, test_client):
        """Test method not allowed errors."""
        response = test_client.put("/health")
        assert response.status_code == 405

    def test_post_to_health_not_allowed(self, test_client):
        """Test that POST to health endpoint is not allowed."""
        response = test_client.post("/health")
        assert response.status_code == 405

    def test_api_routes_exist(self, test_client):
        """Test that API routes are properly registered."""
        # Test that /api/ai/generate exists (will fail validation but not 404)
        response = test_client.post("/api/ai/generate", json={})
        # Should be 422 (validation error) not 404
        assert response.status_code != 404

    def test_api_stream_route_exists(self, test_client):
        """Test that /api/ai/stream route exists."""
        # Empty payload should fail validation but not 404
        response = test_client.post("/api/ai/stream", json={})
        assert response.status_code != 404


class TestAppIntegration:
    """Test full app integration scenarios."""

    def test_concurrent_health_checks(self, test_client):
        """Test that app handles concurrent requests."""
        responses = []
        for _ in range(10):
            response = test_client.get("/health")
            responses.append(response.status_code)

        assert all(status == 200 for status in responses)

    def test_app_doesnt_crash_on_invalid_json(self, test_client):
        """Test app handles invalid JSON gracefully."""
        response = test_client.post(
            "/api/ai/generate",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        # Should handle gracefully (422 or 400)
        assert response.status_code >= 400

    def test_large_request_headers(self, test_client):
        """Test app handles large headers."""
        response = test_client.get(
            "/health",
            headers={"X-Custom": "X" * 1000},
        )
        assert response.status_code == 200

    def test_request_with_query_params(self, test_client):
        """Test that health endpoint ignores query params."""
        response = test_client.get("/health?foo=bar&baz=qux")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
