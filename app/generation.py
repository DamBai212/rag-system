from __future__ import annotations

from typing import Mapping


GROUNDING_INSTRUCTIONS = (
    "You are a retrieval-augmented assistant. Answer using only the provided "
    "context. If the context is incomplete or does not contain the answer, say "
    "so clearly. Keep the answer concise and practical."
)
SOURCE_EXCERPT_MAX_CHARS = 240


def format_context_chunks(chunks: list[Mapping[str, object]]) -> str:
    if not chunks:
        raise ValueError("At least one retrieved chunk is required.")

    sections = []
    for index, chunk in enumerate(chunks, start=1):
        text = str(chunk.get("text") or "").strip()
        if not text:
            raise ValueError("Retrieved chunks must include non-empty text.")

        source = chunk.get("source") or "unknown"
        chunk_index = chunk.get("chunk_index")
        score = chunk.get("score")
        score_text = f"{score:.3f}" if isinstance(score, (int, float)) else "n/a"

        sections.append(
            f"[Chunk {index}] id={chunk.get('id')} source={source} "
            f"chunk_index={chunk_index} score={score_text}\n{text}"
        )

    return "\n\n".join(sections)


def build_grounded_prompt(question: str, chunks: list[Mapping[str, object]]) -> str:
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Question must not be empty.")

    context = format_context_chunks(chunks)
    return (
        f"Question:\n{cleaned_question}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Write an answer grounded in the retrieved context. If the context does "
        "not fully answer the question, explain what is missing instead of "
        "guessing."
    )


def build_source_excerpt(
    text: object,
    *,
    max_chars: int = SOURCE_EXCERPT_MAX_CHARS,
) -> str | None:
    cleaned_text = " ".join(str(text or "").split())
    if not cleaned_text:
        return None

    if max_chars <= 3 or len(cleaned_text) <= max_chars:
        return cleaned_text[:max_chars] if max_chars > 0 else None

    truncated = cleaned_text[: max_chars - 3].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return f"{truncated}..."


def collect_sources(chunks: list[Mapping[str, object]]) -> list[dict[str, object]]:
    sources = []
    seen_ids: set[str] = set()

    for chunk in chunks:
        chunk_id = str(chunk.get("id"))
        if chunk_id in seen_ids:
            continue

        seen_ids.add(chunk_id)
        sources.append(
            {
                "id": chunk.get("id"),
                "source": chunk.get("source"),
                "chunk_index": chunk.get("chunk_index"),
                "score": chunk.get("score"),
                "excerpt": build_source_excerpt(chunk.get("text")),
            }
        )

    return sources


def generate_grounded_answer(
    client,
    model: str,
    question: str,
    chunks: list[Mapping[str, object]],
    max_output_tokens: int = 400,
    instructions: str = GROUNDING_INSTRUCTIONS,
) -> dict[str, object]:
    if max_output_tokens <= 0:
        raise ValueError("max_output_tokens must be greater than 0.")

    prompt = build_grounded_prompt(question, chunks)
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=prompt,
        max_output_tokens=max_output_tokens,
    )

    answer_text = str(getattr(response, "output_text", "") or "").strip()
    if not answer_text:
        raise ValueError("OpenAI response did not include output text.")

    return {
        "answer": answer_text,
        "sources": collect_sources(chunks),
        "model": getattr(response, "model", model),
        "response_id": getattr(response, "id", None),
    }
