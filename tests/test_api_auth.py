import pytest
from fastapi.testclient import TestClient

from app.api import SESSION_COOKIE_NAME, create_app
from app.config import ApiSettings
from app.config import ObservabilitySettings
from app.password_auth import hash_password
from app.session_auth import create_signed_session_value, verify_signed_session_value


def test_api_settings_defaults_to_no_auth(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RAG_API_TOKEN", raising=False)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    monkeypatch.delenv("SESSION_USERNAME", raising=False)
    monkeypatch.delenv("SESSION_PASSWORD_HASH", raising=False)
    monkeypatch.delenv("SESSION_TTL_SECONDS", raising=False)
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)

    settings = ApiSettings.from_env()

    assert settings.api_token is None
    assert settings.auth_enabled() is False
    assert settings.session_secret is None
    assert settings.session_username is None
    assert settings.session_password_hash is None
    assert settings.session_ttl_seconds == 43200
    assert settings.session_cookie_secure is False


def test_api_settings_reads_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_API_TOKEN", "secret-token")
    monkeypatch.setenv("SESSION_SECRET", "cookie-secret")
    monkeypatch.delenv("SESSION_USERNAME", raising=False)
    monkeypatch.delenv("SESSION_PASSWORD_HASH", raising=False)
    monkeypatch.setenv("SESSION_TTL_SECONDS", "1800")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")

    settings = ApiSettings.from_env()

    assert settings.api_token == "secret-token"
    assert settings.auth_enabled() is True
    assert settings.session_secret == "cookie-secret"
    assert settings.session_ttl_seconds == 1800
    assert settings.session_cookie_secure is True


def test_api_settings_reads_dedicated_session_credentials(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("RAG_API_TOKEN", raising=False)
    monkeypatch.setenv("SESSION_USERNAME", "ops")
    monkeypatch.setenv("SESSION_PASSWORD_HASH", hash_password("strong-password"))
    monkeypatch.setenv("SESSION_SECRET", "cookie-secret")
    monkeypatch.delenv("SESSION_TTL_SECONDS", raising=False)
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)

    settings = ApiSettings.from_env()

    assert settings.api_token is None
    assert settings.session_username == "ops"
    assert settings.session_auth_enabled() is True
    assert settings.request_auth_enabled() is True
    assert settings.auth_enabled() is True


def test_api_settings_requires_complete_session_credentials(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("RAG_API_TOKEN", raising=False)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    monkeypatch.setenv("SESSION_USERNAME", "ops")
    monkeypatch.delenv("SESSION_PASSWORD_HASH", raising=False)

    with pytest.raises(ValueError, match="Set both SESSION_USERNAME and SESSION_PASSWORD_HASH together."):
        ApiSettings.from_env()


def test_signed_session_value_verifies_and_expires():
    settings = ApiSettings(
        api_token="secret-token",
        session_secret="cookie-secret",
        session_ttl_seconds=60,
        session_cookie_secure=False,
    )

    session_value = create_signed_session_value(settings, now=100)

    assert verify_signed_session_value(session_value, settings, now=120) is True
    assert verify_signed_session_value(session_value, settings, now=161) is False


def test_signed_session_value_rejects_tampering():
    settings = ApiSettings(
        api_token="secret-token",
        session_secret="cookie-secret",
        session_ttl_seconds=60,
        session_cookie_secure=False,
    )

    session_value = create_signed_session_value(settings, now=100)
    tampered = session_value.replace("v1.", "v1.999999.")

    assert verify_signed_session_value(tampered, settings, now=120) is False


def test_create_session_sets_cookie():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(
                api_token="secret-token",
                session_secret="cookie-secret",
                session_ttl_seconds=3600,
                session_cookie_secure=True,
            ),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.post("/session", json={"token": "secret-token"})

    assert response.status_code == 200
    assert response.json() == {
        "auth_enabled": True,
        "authenticated": True,
        "session_login_enabled": False,
        "token_login_enabled": True,
    }
    assert SESSION_COOKIE_NAME in response.cookies
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "Secure" in response.headers["set-cookie"]


def test_create_session_accepts_username_and_password():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(
                api_token=None,
                session_secret="cookie-secret",
                session_username="ops",
                session_password_hash=hash_password("strong-password"),
                session_ttl_seconds=3600,
                session_cookie_secure=False,
            ),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.post(
        "/session",
        json={"username": "ops", "password": "strong-password"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "auth_enabled": True,
        "authenticated": True,
        "session_login_enabled": True,
        "token_login_enabled": False,
    }
    assert SESSION_COOKIE_NAME in response.cookies


def test_auth_status_uses_session_cookie():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(
                api_token="secret-token",
                session_secret="cookie-secret",
                session_ttl_seconds=3600,
                session_cookie_secure=False,
            ),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    client.post("/session", json={"token": "secret-token"})
    response = client.get("/auth/status")

    assert response.status_code == 200
    assert response.json() == {
        "auth_enabled": True,
        "authenticated": True,
        "session_login_enabled": False,
        "token_login_enabled": True,
    }
