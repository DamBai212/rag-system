from __future__ import annotations

from typing import Callable, Mapping

from app.generation import generate_grounded_answer
from app.retrieval import search_chunks


class NoRetrievedChunksError(ValueError):
    pass


def run_rag_pipeline(
    elastic_client,
    openai_client,
    *,
    question: str,
    index_name: str,
    model: str,
    top_k: int = 3,
    max_output_tokens: int = 400,
    search_fn: Callable[..., list[Mapping[str, object]]] = search_chunks,
    generate_fn: Callable[..., dict[str, object]] = generate_grounded_answer,
) -> dict[str, object]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    chunks = search_fn(
        elastic_client,
        index_name=index_name,
        query=question,
        top_k=top_k,
    )

    if not chunks:
        raise NoRetrievedChunksError(
            f"No retrieved chunks found for question: {question}"
        )

    result = generate_fn(
        openai_client,
        model=model,
        question=question,
        chunks=chunks,
        max_output_tokens=max_output_tokens,
    )

    return {
        "question": question,
        "answer": result["answer"],
        "sources": result["sources"],
        "model": result["model"],
        "response_id": result["response_id"],
        "retrieved_chunk_count": len(chunks),
    }
