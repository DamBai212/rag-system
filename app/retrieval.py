from __future__ import annotations

from typing import Mapping


def build_text_match_query(query: str) -> dict[str, object]:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Query must not be empty.")

    return {
        "match": {
            "text": {
                "query": cleaned_query,
            }
        }
    }


def normalize_search_hit(hit: Mapping[str, object]) -> dict[str, object]:
    source = hit.get("_source", {})
    if not isinstance(source, dict):
        source = {}

    return {
        "id": source.get("id") or hit.get("_id"),
        "text": source.get("text"),
        "source": source.get("source"),
        "chunk_index": source.get("chunk_index"),
        "score": hit.get("_score"),
    }


def search_chunks(
    client,
    index_name: str,
    query: str,
    top_k: int = 5,
) -> list[dict[str, object]]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    response = client.search(
        index=index_name,
        size=top_k,
        query=build_text_match_query(query),
    )

    hits = response.get("hits", {}).get("hits", [])
    return [normalize_search_hit(hit) for hit in hits]
