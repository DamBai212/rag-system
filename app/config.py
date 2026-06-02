from __future__ import annotations

import os
from dataclasses import dataclass

VALID_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}


def _read_optional_env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def _parse_positive_int(name: str, value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc

    if parsed <= 0:
        raise ValueError(f"{name} must be greater than 0.")

    return parsed


def _parse_log_level(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in VALID_LOG_LEVELS:
        expected = ", ".join(sorted(VALID_LOG_LEVELS))
        raise ValueError(f"LOG_LEVEL must be one of: {expected}.")
    return normalized


@dataclass(frozen=True)
class ElasticsearchSettings:
    cloud_id: str | None
    endpoint: str | None
    api_key: str | None
    username: str | None
    password: str | None
    index_name: str = "rag-docs"
    request_timeout: int = 30
    verify_certs: bool = True

    @classmethod
    def from_env(cls) -> "ElasticsearchSettings":
        cloud_id = _read_optional_env("ELASTIC_CLOUD_ID")
        endpoint = _read_optional_env("ELASTIC_ENDPOINT")
        api_key = _read_optional_env("ELASTIC_API_KEY")
        username = _read_optional_env("ELASTIC_USERNAME")
        password = _read_optional_env("ELASTIC_PASSWORD")
        index_name = _read_optional_env("ELASTIC_INDEX") or "rag-docs"
        timeout_raw = os.getenv("ELASTIC_REQUEST_TIMEOUT", "30").strip()
        verify_raw = os.getenv("ELASTIC_VERIFY_CERTS", "true")

        if not cloud_id and not endpoint:
            raise ValueError(
                "Set ELASTIC_CLOUD_ID or ELASTIC_ENDPOINT before connecting."
            )

        if not api_key and not (username and password):
            raise ValueError(
                "Set ELASTIC_API_KEY or both ELASTIC_USERNAME and ELASTIC_PASSWORD."
            )

        request_timeout = _parse_positive_int("ELASTIC_REQUEST_TIMEOUT", timeout_raw)
        verify_certs = _parse_bool(verify_raw)

        return cls(
            cloud_id=cloud_id,
            endpoint=endpoint,
            api_key=api_key,
            username=username,
            password=password,
            index_name=index_name,
            request_timeout=request_timeout,
            verify_certs=verify_certs,
        )

    def client_options(self) -> dict[str, object]:
        options: dict[str, object] = {
            "request_timeout": self.request_timeout,
            "verify_certs": self.verify_certs,
        }

        if self.cloud_id:
            options["cloud_id"] = self.cloud_id
        elif self.endpoint:
            options["hosts"] = [self.endpoint]
        else:
            raise ValueError("An Elasticsearch connection target is required.")

        if self.api_key:
            options["api_key"] = self.api_key
        elif self.username and self.password:
            options["basic_auth"] = (self.username, self.password)
        else:
            raise ValueError("Elasticsearch authentication is not configured.")

        return options

    def target(self) -> str:
        if self.cloud_id:
            return self.cloud_id
        if self.endpoint:
            return self.endpoint
        raise ValueError("An Elasticsearch connection target is required.")


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str
    model: str = "gpt-4o-mini"
    max_output_tokens: int = 400

    @classmethod
    def from_env(cls) -> "OpenAISettings":
        api_key = _read_optional_env("OPENAI_API_KEY")
        model = _read_optional_env("OPENAI_MODEL") or "gpt-4o-mini"
        max_tokens_raw = os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "400").strip()

        if not api_key:
            raise ValueError("Set OPENAI_API_KEY before generating responses.")

        max_output_tokens = _parse_positive_int(
            "OPENAI_MAX_OUTPUT_TOKENS",
            max_tokens_raw,
        )

        return cls(
            api_key=api_key,
            model=model,
            max_output_tokens=max_output_tokens,
        )

    def client_options(self) -> dict[str, object]:
        return {"api_key": self.api_key}


@dataclass(frozen=True)
class ApiSettings:
    api_token: str | None = None

    @classmethod
    def from_env(cls) -> "ApiSettings":
        return cls(api_token=_read_optional_env("RAG_API_TOKEN"))

    def auth_enabled(self) -> bool:
        return bool(self.api_token)


@dataclass(frozen=True)
class ObservabilitySettings:
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "ObservabilitySettings":
        log_level = _parse_log_level(os.getenv("LOG_LEVEL", "INFO"))
        return cls(log_level=log_level)
