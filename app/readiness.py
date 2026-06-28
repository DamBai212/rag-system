from __future__ import annotations

from typing import Callable

from app.config import ApiSettings, ElasticsearchSettings, OpenAISettings
from app.elasticsearch_client import ping_elasticsearch
from app.openai_client import create_openai_client


def describe_auth_mode(settings: ApiSettings) -> str:
    if settings.session_auth_enabled() and settings.api_token_auth_enabled():
        return "Dedicated browser session auth and bearer token auth are configured."
    if settings.session_auth_enabled():
        return "Dedicated browser session auth is configured."
    if settings.api_token_auth_enabled():
        return "Bearer token auth is configured."
    return "Auth is disabled."


def build_readiness_report(
    elasticsearch_settings_loader: Callable[
        [], ElasticsearchSettings
    ] = ElasticsearchSettings.from_env,
    elasticsearch_ping: Callable[[ElasticsearchSettings], bool] = ping_elasticsearch,
    openai_settings_loader: Callable[[], OpenAISettings] = OpenAISettings.from_env,
    openai_client_factory: Callable[[OpenAISettings], object] = create_openai_client,
    api_settings_loader: Callable[[], ApiSettings] = ApiSettings.from_env,
) -> dict[str, object]:
    checks: dict[str, dict[str, str]] = {}
    ready = True

    try:
        elasticsearch_settings = elasticsearch_settings_loader()
        if not elasticsearch_ping(elasticsearch_settings):
            raise RuntimeError("Elasticsearch ping failed.")
        checks["elasticsearch"] = {
            "status": "ok",
            "detail": "Elasticsearch connectivity verified.",
        }
    except Exception as exc:
        checks["elasticsearch"] = {
            "status": "error",
            "detail": str(exc),
        }
        ready = False

    try:
        openai_settings = openai_settings_loader()
        openai_client_factory(openai_settings)
        checks["openai"] = {
            "status": "ok",
            "detail": f"OpenAI client configured for model {openai_settings.model}.",
        }
    except Exception as exc:
        checks["openai"] = {
            "status": "error",
            "detail": str(exc),
        }
        ready = False

    try:
        api_settings = api_settings_loader()
        checks["auth"] = {
            "status": "ok",
            "detail": describe_auth_mode(api_settings),
        }
    except Exception as exc:
        checks["auth"] = {
            "status": "error",
            "detail": str(exc),
        }
        ready = False

    return {
        "status": "ready" if ready else "degraded",
        "checks": checks,
    }
