from __future__ import annotations

from app.config import OpenAISettings


def create_openai_client(settings: OpenAISettings | None = None):
    settings = settings or OpenAISettings.from_env()

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The `openai` package is not installed. "
            "Install the project dependencies before generating responses."
        ) from exc

    return OpenAI(**settings.client_options())
