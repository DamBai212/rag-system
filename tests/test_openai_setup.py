import sys
import types

import pytest

from app.config import OpenAISettings
from app.openai_client import create_openai_client


OPENAI_ENV_VARS = [
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_MAX_OUTPUT_TOKENS",
]


def clear_openai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in OPENAI_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_openai_settings_from_env_defaults(monkeypatch: pytest.MonkeyPatch):
    clear_openai_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")

    settings = OpenAISettings.from_env()

    assert settings.api_key == "test-api-key"
    assert settings.model == "gpt-4o-mini"
    assert settings.max_output_tokens == 400


def test_openai_settings_from_env_supports_overrides(
    monkeypatch: pytest.MonkeyPatch,
):
    clear_openai_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")
    monkeypatch.setenv("OPENAI_MAX_OUTPUT_TOKENS", "250")

    settings = OpenAISettings.from_env()

    assert settings.model == "gpt-4.1-mini"
    assert settings.max_output_tokens == 250


def test_openai_settings_requires_api_key(monkeypatch: pytest.MonkeyPatch):
    clear_openai_env(monkeypatch)

    with pytest.raises(ValueError, match="Set OPENAI_API_KEY"):
        OpenAISettings.from_env()


def test_openai_settings_validates_max_output_tokens(
    monkeypatch: pytest.MonkeyPatch,
):
    clear_openai_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENAI_MAX_OUTPUT_TOKENS", "0")

    with pytest.raises(ValueError, match="greater than 0"):
        OpenAISettings.from_env()


def test_create_openai_client_uses_settings(monkeypatch: pytest.MonkeyPatch):
    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setitem(
        sys.modules,
        "openai",
        types.SimpleNamespace(OpenAI=FakeOpenAI),
    )

    settings = OpenAISettings(api_key="test-api-key")

    client = create_openai_client(settings)

    assert client.kwargs["api_key"] == "test-api-key"
