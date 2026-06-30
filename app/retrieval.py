from __future__ import annotations

from typing import Mapping, Sequence


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


def normalize_source_filters(sources: Sequence[str] | None) -> list[str]:
    if not sources:
        return []

    normalized: list[str] = []
    seen: set[str] = set()

    for source in sources:
        cleaned_source = source.strip()
        if not cleaned_source or cleaned_source in seen:
            continue
        normalized.append(cleaned_source)
        seen.add(cleaned_source)

    return normalized


def build_chunk_search_query(
    query: str,
    sources: Sequence[str] | None = None,
) -> dict[str, object]:
    text_query = build_text_match_query(query)
    normalized_sources = normalize_source_filters(sources)

    if not normalized_sources:
        return text_query

    return {
        "bool": {
            "must": [text_query],
            "filter": [
                {
                    "terms": {
                        "source": normalized_sources,
                    }
                }
            ],
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
    sources: Sequence[str] | None = None,
) -> list[dict[str, object]]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    response = client.search(
        index=index_name,
        size=top_k,
        query=build_chunk_search_query(query, sources=sources),
    )

    hits = response.get("hits", {}).get("hits", [])
    return [normalize_search_hit(hit) for hit in hits]


def list_index_sources(
    client,
    index_name: str,
    size: int = 100,
) -> list[str]:
    if size <= 0:
        raise ValueError("size must be greater than 0.")

    response = client.search(
        index=index_name,
        size=0,
        aggs={
            "sources": {
                "terms": {
                    "field": "source",
                    "size": size,
                    "order": {"_key": "asc"},
                }
            }
        },
    )

    buckets = response.get("aggregations", {}).get("sources", {}).get("buckets", [])
    return [
        bucket["key"]
        for bucket in buckets
        if isinstance(bucket, dict) and isinstance(bucket.get("key"), str)
    ]
