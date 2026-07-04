from fastapi.testclient import TestClient

from app.api import SESSION_COOKIE_NAME, create_app
from app.config import ApiSettings, ObservabilitySettings, RateLimitSettings
from app.observability import REQUEST_ID_HEADER
from app.password_auth import hash_password
from app.pipeline import NoRetrievedChunksError
from app.rate_limit import InMemoryRateLimiter


def test_health_endpoint_returns_ok():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(api_token="secret-token"),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers[REQUEST_ID_HEADER]


def test_ready_endpoint_returns_readiness_report():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(api_token="secret-token"),
            observability_settings=ObservabilitySettings(log_level="INFO"),
            readiness_checker=lambda: {
                "status": "ready",
                "checks": {
                    "elasticsearch": {
                        "status": "ok",
                        "detail": "Elasticsearch connectivity verified.",
                    },
                    "openai": {
                        "status": "ok",
                        "detail": "OpenAI client configured for model gpt-4o-mini.",
                    },
                    "auth": {
                        "status": "ok",
                        "detail": "Bearer token auth is configured.",
                    },
                },
            },
        )
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"]["elasticsearch"]["status"] == "ok"
    assert response.headers[REQUEST_ID_HEADER]


def test_ready_endpoint_returns_503_when_degraded():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(api_token="secret-token"),
            observability_settings=ObservabilitySettings(log_level="INFO"),
            readiness_checker=lambda: {
                "status": "degraded",
                "checks": {
                    "elasticsearch": {
                        "status": "error",
                        "detail": "Elasticsearch ping failed.",
                    },
                    "openai": {
                        "status": "ok",
                        "detail": "OpenAI client configured for model gpt-4o-mini.",
                    },
                    "auth": {
                        "status": "ok",
                        "detail": "Bearer token auth is configured.",
                    },
                },
            },
        )
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.headers[REQUEST_ID_HEADER]


def test_sources_endpoint_returns_source_catalog():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(api_token=None),
            observability_settings=ObservabilitySettings(log_level="INFO"),
            source_lister=lambda: ["docs.txt", "faq.txt"],
        )
    )

    response = client.get("/sources")

    assert response.status_code == 200
    assert response.json() == {"sources": ["docs.txt", "faq.txt"]}
    assert response.headers[REQUEST_ID_HEADER]


def test_sources_endpoint_requires_same_auth_as_ask():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(api_token="secret-token"),
            observability_settings=ObservabilitySettings(log_level="INFO"),
            source_lister=lambda: ["docs.txt"],
        )
    )

    unauthorized = client.get("/sources")
    assert unauthorized.status_code == 401

    authorized = client.get(
        "/sources",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert authorized.status_code == 200
    assert authorized.json() == {"sources": ["docs.txt"]}


def test_ask_endpoint_returns_pipeline_response():
    captured = {}

    def fake_rag_runner(**kwargs):
        captured.update(kwargs)
        return {
            "question": kwargs["question"],
            "answer": "Grounded answer",
            "sources": [
                {
                    "id": "docs_0",
                    "source": "docs.txt",
                    "chunk_index": 0,
                    "score": 1.5,
                }
            ],
            "model": "gpt-4o-mini",
            "response_id": "resp_123",
            "retrieved_chunk_count": 1,
        }

    client = TestClient(
        create_app(
            rag_runner=fake_rag_runner,
            api_settings=ApiSettings(api_token="secret-token"),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.post(
        "/ask",
        json={"question": "What is RAG?", "top_k": 3},
        headers={"Authorization": "Bearer secret-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "question": "What is RAG?",
        "answer": "Grounded answer",
        "sources": [
            {
                "id": "docs_0",
                "source": "docs.txt",
                "chunk_index": 0,
                "score": 1.5,
            }
        ],
        "model": "gpt-4o-mini",
        "response_id": "resp_123",
        "retrieved_chunk_count": 1,
    }
    assert captured == {
        "question": "What is RAG?",
        "top_k": 3,
        "sources": [],
        "index": None,
        "model": None,
    }
    assert response.headers[REQUEST_ID_HEADER]


def test_ask_endpoint_passes_source_filters_to_rag_runner():
    captured = {}

    def fake_rag_runner(**kwargs):
        captured.update(kwargs)
        return {
            "question": kwargs["question"],
            "answer": "Grounded answer",
            "sources": [],
            "model": "gpt-4o-mini",
            "response_id": None,
            "retrieved_chunk_count": 0,
        }

    client = TestClient(
        create_app(
            rag_runner=fake_rag_runner,
            api_settings=ApiSettings(api_token=None),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.post(
        "/ask",
        json={
            "question": "What changed in the latest release?",
            "top_k": 3,
            "sources": ["release-notes.txt"],
        },
    )

    assert response.status_code == 200
    assert captured["sources"] == ["release-notes.txt"]


def test_ask_endpoint_returns_404_when_no_chunks_found():
    def fake_rag_runner(**kwargs):
        raise NoRetrievedChunksError("No retrieved chunks found for question: What is RAG?")

    client = TestClient(
        create_app(
            rag_runner=fake_rag_runner,
            api_settings=ApiSettings(api_token="secret-token"),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.post(
        "/ask",
        json={"question": "What is RAG?"},
        headers={"Authorization": "Bearer secret-token"},
    )

    assert response.status_code == 404
    assert response.headers[REQUEST_ID_HEADER]


def test_ask_endpoint_requires_authorization_when_token_is_configured():
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
            api_settings=ApiSettings(api_token="secret-token"),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.post("/ask", json={"question": "What is RAG?"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing Authorization header."}
    assert response.headers[REQUEST_ID_HEADER]


def test_ask_endpoint_rejects_invalid_authorization_token():
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
            api_settings=ApiSettings(api_token="secret-token"),
            observability_settings=ObservabilitySettings(log_level="INFO"),
        )
    )

    response = client.post(
        "/ask",
        json={"question": "What is RAG?"},
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API token."}
    assert response.headers[REQUEST_ID_HEADER]


def test_ask_endpoint_accepts_authenticated_session_cookie():
    captured = {}

    def fake_rag_runner(**kwargs):
        captured.update(kwargs)
        return {
            "question": kwargs["question"],
            "answer": "Grounded answer",
            "sources": [],
            "model": "gpt-4o-mini",
            "response_id": None,
            "retrieved_chunk_count": 0,
        }

    client = TestClient(
        create_app(
            rag_runner=fake_rag_runner,
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

    response = client.post(
        "/ask",
        json={"question": "What is RAG?"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Grounded answer"
    assert captured["question"] == "What is RAG?"


def test_ask_endpoint_supports_dedicated_session_credentials():
    captured = {}

    def fake_rag_runner(**kwargs):
        captured.update(kwargs)
        return {
            "question": kwargs["question"],
            "answer": "Grounded answer",
            "sources": [],
            "model": "gpt-4o-mini",
            "response_id": None,
            "retrieved_chunk_count": 0,
        }

    client = TestClient(
        create_app(
            rag_runner=fake_rag_runner,
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

    unauthorized = client.post("/ask", json={"question": "What is RAG?"})
    assert unauthorized.status_code == 401
    assert unauthorized.json() == {"detail": "Authentication required."}

    login = client.post(
        "/session",
        json={"username": "ops", "password": "strong-password"},
    )
    assert login.status_code == 200

    response = client.post("/ask", json={"question": "What is RAG?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Grounded answer"
    assert captured["question"] == "What is RAG?"


def test_ask_endpoint_rejects_bearer_token_when_only_session_auth_is_enabled():
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
        "/ask",
        json={"question": "What is RAG?"},
        headers={"Authorization": "Bearer secret-token"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Bearer token auth is not enabled for this deployment."
    }


def test_ask_endpoint_returns_429_when_rate_limit_is_exceeded():
    limiter = InMemoryRateLimiter(
        RateLimitSettings(enabled=True, max_requests=1, window_seconds=60)
    )

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
            rate_limiter=limiter,
        )
    )

    first = client.post("/ask", json={"question": "What is RAG?"})
    second = client.post("/ask", json={"question": "What is RAG?"})

    assert first.status_code == 200
    assert second.status_code == 429
