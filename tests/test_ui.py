from fastapi.testclient import TestClient

from app.api import create_app
from app.config import ApiSettings, ObservabilitySettings


def test_home_page_returns_html():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(api_token=None),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Ask the RAG System" in response.text
    assert "Connected to the local RAG API" in response.text
    assert "X-Request-ID" in response.text
    assert "Sign In" in response.text
    assert "/session" in response.text
