from fastapi.testclient import TestClient

from app.api import create_app
from app.pipeline import NoRetrievedChunksError


def test_health_endpoint_returns_ok():
    client = TestClient(create_app(rag_runner=lambda **kwargs: {}))

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

    client = TestClient(create_app(rag_runner=fake_rag_runner))

    response = client.post(
        "/ask",
        json={"question": "What is RAG?", "top_k": 3},
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

    client = TestClient(create_app(rag_runner=fake_rag_runner))

    response = client.post("/ask", json={"question": "What is RAG?"})

    assert response.status_code == 404
