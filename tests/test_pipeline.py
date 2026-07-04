import pytest

from app.pipeline import NoRetrievedChunksError, run_rag_pipeline


def sample_chunk(**overrides):
    chunk = {
        "id": "docs_0",
        "text": "RAG uses retrieved context before generation.",
        "source": "docs.txt",
        "chunk_index": 0,
        "score": 1.5,
    }
    chunk.update(overrides)
    return chunk


def test_run_rag_pipeline_returns_grounded_answer():
    search_calls = []
    generation_calls = []

    def fake_search(client, **kwargs):
        search_calls.append((client, kwargs))
        return [sample_chunk()]

    def fake_generate(client, **kwargs):
        generation_calls.append((client, kwargs))
        return {
            "answer": "Grounded answer",
            "sources": [
                {
                    "id": "docs_0",
                    "source": "docs.txt",
                    "chunk_index": 0,
                    "score": 1.5,
                }
            ],
            "model": kwargs["model"],
            "response_id": "resp_123",
        }

    result = run_rag_pipeline(
        elastic_client="elastic-client",
        openai_client="openai-client",
        question="What is RAG?",
        index_name="rag-docs",
        model="gpt-4o-mini",
        top_k=3,
        sources=["docs.txt"],
        max_output_tokens=250,
        search_fn=fake_search,
        generate_fn=fake_generate,
    )

    assert result == {
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
    assert search_calls == [
        (
            "elastic-client",
            {
                "index_name": "rag-docs",
                "query": "What is RAG?",
                "top_k": 3,
                "sources": ["docs.txt"],
            },
        )
    ]
    assert generation_calls == [
        (
            "openai-client",
            {
                "model": "gpt-4o-mini",
                "question": "What is RAG?",
                "chunks": [sample_chunk()],
                "max_output_tokens": 250,
            },
        )
    ]


def test_run_rag_pipeline_requires_retrieved_chunks():
    def fake_search(client, **kwargs):
        return []

    def fake_generate(client, **kwargs):
        raise AssertionError("Generation should not run when nothing was retrieved.")

    with pytest.raises(NoRetrievedChunksError, match="No retrieved chunks found"):
        run_rag_pipeline(
            elastic_client="elastic-client",
            openai_client="openai-client",
            question="What is RAG?",
            index_name="rag-docs",
            model="gpt-4o-mini",
            search_fn=fake_search,
            generate_fn=fake_generate,
        )
