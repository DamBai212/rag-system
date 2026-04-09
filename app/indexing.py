from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Iterable, Mapping


REQUIRED_CHUNK_FIELDS = {"id", "text", "source", "chunk_index"}


def load_chunks(filepath: str | Path) -> list[dict[str, object]]:
    path = Path(filepath)
    payload = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(payload, list):
        raise ValueError("Chunk file must contain a JSON list of chunk documents.")

    return payload


def build_chunk_index_config() -> dict[str, object]:
    return {
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "id": {"type": "keyword"},
                "text": {"type": "text"},
                "source": {"type": "keyword"},
                "chunk_index": {"type": "integer"},
            },
        }
    }


def build_index_action(
    index_name: str,
    chunk: Mapping[str, object],
) -> dict[str, object]:
    missing_fields = REQUIRED_CHUNK_FIELDS - set(chunk)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Chunk is missing required fields: {missing}")

    empty_fields = []
    for field in REQUIRED_CHUNK_FIELDS:
        value = chunk[field]
        if value is None:
            empty_fields.append(field)
        elif isinstance(value, str) and not value.strip():
            empty_fields.append(field)

    if empty_fields:
        empty = ", ".join(sorted(empty_fields))
        raise ValueError(f"Chunk has empty required fields: {empty}")

    return {
        "_op_type": "index",
        "_index": index_name,
        "_id": str(chunk["id"]),
        "_source": {
            "id": str(chunk["id"]),
            "text": chunk["text"],
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"],
        },
    }


def build_bulk_index_actions(
    index_name: str,
    chunks: Iterable[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [build_index_action(index_name=index_name, chunk=chunk) for chunk in chunks]


def ensure_index(
    client,
    index_name: str,
    index_config: dict[str, object] | None = None,
) -> bool:
    if client.indices.exists(index=index_name):
        return False

    client.indices.create(index=index_name, **(index_config or build_chunk_index_config()))
    return True


def bulk_index_chunks(
    client,
    index_name: str,
    chunks: Iterable[Mapping[str, object]],
    bulk_fn: Callable[..., tuple[int, list[object]]] | None = None,
) -> tuple[int, list[object]]:
    actions = build_bulk_index_actions(index_name=index_name, chunks=chunks)

    if bulk_fn is None:
        from elasticsearch.helpers import bulk as bulk_fn

    return bulk_fn(
        client,
        actions=actions,
        refresh="wait_for",
        raise_on_error=False,
        raise_on_exception=False,
    )
