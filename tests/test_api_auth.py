import pytest

from app.config import ApiSettings


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
