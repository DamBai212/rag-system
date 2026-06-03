import pytest
from fastapi.testclient import TestClient

from app.api import SESSION_COOKIE_NAME, create_app
from app.config import ApiSettings
from app.config import ObservabilitySettings


def test_api_settings_defaults_to_no_auth(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RAG_API_TOKEN", raising=False)

    settings = ApiSettings.from_env()

    assert settings.api_token is None
    assert settings.auth_enabled() is False


def test_api_settings_reads_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_API_TOKEN", "secret-token")

    settings = ApiSettings.from_env()

    assert settings.api_token == "secret-token"
    assert settings.auth_enabled() is True


def test_create_session_sets_cookie():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(api_token="secret-token"),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.post("/session", json={"token": "secret-token"})

    assert response.status_code == 200
    assert response.json() == {"auth_enabled": True, "authenticated": True}
    assert SESSION_COOKIE_NAME in response.cookies


def test_auth_status_uses_session_cookie():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(api_token="secret-token"),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    client.post("/session", json={"token": "secret-token"})
    response = client.get("/auth/status")

    assert response.status_code == 200
    assert response.json() == {"auth_enabled": True, "authenticated": True}
