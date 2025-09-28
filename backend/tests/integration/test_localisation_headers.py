"""Integration tests for localisation middleware (T052.9)."""

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_accept_language_header_sets_response_language():
    """Localisation middleware should surface detected language via headers."""
    response = client.get(
        "/api/v1/health",
        headers={"Accept-Language": "fr-FR,fr;q=0.9"},
    )

    assert response.status_code == 200
    assert response.headers.get("X-Localisation-Language") == "fr"
    assert "fr" in response.headers.get("X-Localisation-Supported-Languages", "")


def test_default_language_applied_when_header_missing():
    """Default language should be applied when no hints are provided."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers.get("X-Localisation-Language") == "en"
