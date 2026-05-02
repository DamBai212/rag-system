from fastapi.testclient import TestClient

from app.api import create_app
from app.config import ApiSettings
from app.pipeline import NoRetrievedChunksError


def test_health_endpoint_returns_ok():
    client = TestClient(
        create_app(
            rag_runner=lambda **kwargs: {},
            api_settings=ApiSettings(api_token="secret-token"),
        )
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
        "index": None,
        "model": None,
    }


def test_ask_endpoint_returns_404_when_no_chunks_found():
    def fake_rag_runner(**kwargs):
        raise NoRetrievedChunksError("No retrieved chunks found for question: What is RAG?")

    client = TestClient(
        create_app(
            rag_runner=fake_rag_runner,
            api_settings=ApiSettings(api_token="secret-token"),
        )
    )

    response = client.post(
        "/ask",
        json={"question": "What is RAG?"},
        headers={"Authorization": "Bearer secret-token"},
    )

    assert response.status_code == 404


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
        )
    )

    response = client.post("/ask", json={"question": "What is RAG?"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing Authorization header."}


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
        )
    )

    response = client.post(
        "/ask",
        json={"question": "What is RAG?"},
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API token."}
