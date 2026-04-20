from types import SimpleNamespace

import pytest

from app.generation import (
    build_grounded_prompt,
    collect_sources,
    format_context_chunks,
    generate_grounded_answer,
)


def sample_chunk(**overrides):
    chunk = {
        "id": "docs_0",
        "text": "RAG retrieves relevant context before answer generation.",
        "source": "docs.txt",
        "chunk_index": 0,
        "score": 1.25,
    }
    chunk.update(overrides)
    return chunk


def test_format_context_chunks_includes_metadata():
    context = format_context_chunks([sample_chunk()])

    assert "[Chunk 1]" in context
    assert "source=docs.txt" in context
    assert "score=1.250" in context
    assert "RAG retrieves relevant context" in context


def test_build_grounded_prompt_requires_question():
    with pytest.raises(ValueError, match="Question must not be empty"):
        build_grounded_prompt("   ", [sample_chunk()])


def test_build_grounded_prompt_includes_question_and_context():
    prompt = build_grounded_prompt("What is RAG?", [sample_chunk()])

    assert "Question:\nWhat is RAG?" in prompt
    assert "Retrieved context:" in prompt
    assert "RAG retrieves relevant context" in prompt


def test_collect_sources_deduplicates_by_chunk_id():
    sources = collect_sources(
        [
            sample_chunk(id="docs_0"),
            sample_chunk(id="docs_0", score=0.5),
            sample_chunk(id="docs_1", chunk_index=1),
        ]
    )

    assert [source["id"] for source in sources] == ["docs_0", "docs_1"]


def test_generate_grounded_answer_calls_openai_responses_api():
    class FakeResponsesApi:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(
                id="resp_123",
                model=kwargs["model"],
                output_text="RAG retrieves context before generating the answer.",
            )

    responses_api = FakeResponsesApi()
    client = SimpleNamespace(responses=responses_api)

    result = generate_grounded_answer(
        client,
        model="gpt-4o-mini",
        question="What is RAG?",
        chunks=[sample_chunk()],
        max_output_tokens=250,
    )

    assert result["answer"] == "RAG retrieves context before generating the answer."
    assert result["model"] == "gpt-4o-mini"
    assert result["response_id"] == "resp_123"
    assert responses_api.calls == [
        {
            "model": "gpt-4o-mini",
            "instructions": (
                "You are a retrieval-augmented assistant. Answer using only the "
                "provided context. If the context is incomplete or does not "
                "contain the answer, say so clearly. Keep the answer concise and "
                "practical."
            ),
            "input": (
                "Question:\nWhat is RAG?\n\nRetrieved context:\n"
                "[Chunk 1] id=docs_0 source=docs.txt chunk_index=0 "
                "score=1.250\nRAG retrieves relevant context before answer "
                "generation.\n\nWrite an answer grounded in the retrieved "
                "context. If the context does not fully answer the question, "
                "explain what is missing instead of guessing."
            ),
            "max_output_tokens": 250,
        }
    ]


def test_generate_grounded_answer_requires_output_text():
    class FakeResponsesApi:
        def create(self, **kwargs):
            return SimpleNamespace(id="resp_123", model=kwargs["model"], output_text="")

    client = SimpleNamespace(responses=FakeResponsesApi())

    with pytest.raises(ValueError, match="did not include output text"):
        generate_grounded_answer(
            client,
            model="gpt-4o-mini",
            question="What is RAG?",
            chunks=[sample_chunk()],
        )
