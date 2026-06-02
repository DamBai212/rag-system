import json
import logging

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.config import ApiSettings, ObservabilitySettings
from app.observability import API_LOGGER_NAME, REQUEST_ID_HEADER


def test_observability_settings_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = ObservabilitySettings.from_env()

    assert settings.log_level == "INFO"


def test_observability_settings_validates_log_level(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("LOG_LEVEL", "verbose")

    with pytest.raises(ValueError, match="LOG_LEVEL must be one of"):
        ObservabilitySettings.from_env()


def test_api_returns_generated_request_id_header():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {
                "question": kwargs["question"],
                "answer": "Grounded answer",
                "sources": [],
                "model": "gpt-4o-mini",
                "response_id": None,
                "retrieved_chunk_count": 0,
            },
            api_settings=ApiSettings(api_token=None),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER]


def test_api_preserves_incoming_request_id_header():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {
                "question": kwargs["question"],
                "answer": "Grounded answer",
                "sources": [],
                "model": "gpt-4o-mini",
                "response_id": None,
                "retrieved_chunk_count": 0,
            },
            api_settings=ApiSettings(api_token=None),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.post(
        "/ask",
        json={"question": "What is RAG?"},
        headers={REQUEST_ID_HEADER: "req-123"},
    )

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "req-123"


def test_api_logs_completed_requests(caplog: pytest.LogCaptureFixture):
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {
                "question": kwargs["question"],
                "answer": "Grounded answer",
                "sources": [],
                "model": "gpt-4o-mini",
                "response_id": None,
                "retrieved_chunk_count": 0,
            },
            api_settings=ApiSettings(api_token=None),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    caplog.set_level(logging.INFO, logger=API_LOGGER_NAME)

    response = client.get("/health", headers={REQUEST_ID_HEADER: "req-log"})

    assert response.status_code == 200
    log_record = next(
        record for record in caplog.records if record.name == API_LOGGER_NAME
    )
    payload = json.loads(log_record.getMessage())
    assert payload["event"] == "api_request_completed"
    assert payload["request_id"] == "req-log"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
