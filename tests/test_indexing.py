import json

import pytest

from app.indexing import (
    build_bulk_index_actions,
    build_chunk_index_config,
    build_index_action,
    bulk_index_chunks,
    ensure_index,
    load_chunks,
)


def sample_chunk(**overrides):
    chunk = {
        "id": "docs_0",
        "text": "Retrieval augmented generation improves grounding.",
        "source": "docs.txt",
        "chunk_index": 0,
    }
    chunk.update(overrides)
    return chunk


def test_load_chunks_reads_json_list(tmp_path):
    chunk_file = tmp_path / "chunks.json"
    chunk_file.write_text(json.dumps([sample_chunk()]), encoding="utf-8")

    chunks = load_chunks(chunk_file)

    assert chunks == [sample_chunk()]


def test_load_chunks_requires_json_list(tmp_path):
    chunk_file = tmp_path / "chunks.json"
    chunk_file.write_text(json.dumps({"id": "docs_0"}), encoding="utf-8")

    with pytest.raises(ValueError, match="JSON list"):
        load_chunks(chunk_file)


def test_build_chunk_index_config_contains_expected_fields():
    config = build_chunk_index_config()
    properties = config["mappings"]["properties"]

    assert config["mappings"]["dynamic"] == "strict"
    assert properties["id"]["type"] == "keyword"
    assert properties["text"]["type"] == "text"
    assert properties["source"]["type"] == "keyword"
    assert properties["chunk_index"]["type"] == "integer"


def test_build_index_action_uses_chunk_id():
    action = build_index_action("rag-docs", sample_chunk())

    assert action["_index"] == "rag-docs"
    assert action["_id"] == "docs_0"
    assert action["_source"]["id"] == "docs_0"


def test_build_index_action_requires_all_fields():
    with pytest.raises(ValueError, match="empty required fields: source"):
        build_index_action("rag-docs", sample_chunk(source=None))


def test_build_bulk_index_actions_preserves_order():
    actions = build_bulk_index_actions(
        "rag-docs",
        [sample_chunk(id="docs_0"), sample_chunk(id="docs_1", chunk_index=1)],
    )

    assert [action["_id"] for action in actions] == ["docs_0", "docs_1"]


def test_ensure_index_creates_missing_index():
    class FakeIndices:
        def __init__(self):
            self.created = None

        def exists(self, index):
            return False

        def create(self, index, **kwargs):
            self.created = {"index": index, "kwargs": kwargs}

    class FakeClient:
        def __init__(self):
            self.indices = FakeIndices()

    client = FakeClient()

    created = ensure_index(client, "rag-docs")

    assert created is True
    assert client.indices.created["index"] == "rag-docs"
    assert client.indices.created["kwargs"]["mappings"]["properties"]["text"]["type"] == "text"


def test_ensure_index_skips_existing_index():
    class FakeIndices:
        def exists(self, index):
            return True

    class FakeClient:
        def __init__(self):
            self.indices = FakeIndices()

    client = FakeClient()

    created = ensure_index(client, "rag-docs")

    assert created is False


def test_bulk_index_chunks_calls_bulk_helper():
    captured = {}

    def fake_bulk(client, actions, **kwargs):
        captured["client"] = client
        captured["actions"] = actions
        captured["kwargs"] = kwargs
        return len(actions), []

    client = object()
    chunks = [sample_chunk(), sample_chunk(id="docs_1", chunk_index=1)]

    indexed_count, errors = bulk_index_chunks(
        client,
        index_name="rag-docs",
        chunks=chunks,
        bulk_fn=fake_bulk,
    )

    assert indexed_count == 2
    assert errors == []
    assert captured["client"] is client
    assert [action["_id"] for action in captured["actions"]] == ["docs_0", "docs_1"]
    assert captured["kwargs"]["refresh"] == "wait_for"
    assert captured["kwargs"]["raise_on_error"] is False
