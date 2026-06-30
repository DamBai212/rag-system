import pytest

from app.retrieval import (
    build_chunk_search_query,
    build_text_match_query,
    list_index_sources,
    normalize_source_filters,
    normalize_search_hit,
    search_chunks,
)


def test_build_text_match_query_strips_whitespace():
    query = build_text_match_query("  what is rag?  ")

    assert query == {
        "match": {
            "text": {
                "query": "what is rag?",
            }
        }
    }


def test_build_text_match_query_requires_text():
    with pytest.raises(ValueError, match="must not be empty"):
        build_text_match_query("   ")


def test_normalize_source_filters_strips_empty_values_and_deduplicates():
    sources = normalize_source_filters([" docs.txt ", "", "docs.txt", "faq.txt"])

    assert sources == ["docs.txt", "faq.txt"]


def test_build_chunk_search_query_supports_source_filters():
    query = build_chunk_search_query(
        "What is RAG?",
        sources=[" docs.txt ", "faq.txt"],
    )

    assert query == {
        "bool": {
            "must": [
                {
                    "match": {
                        "text": {
                            "query": "What is RAG?",
                        }
                    }
                }
            ],
            "filter": [
                {
                    "terms": {
                        "source": ["docs.txt", "faq.txt"],
                    }
                }
            ],
        }
    }


def test_normalize_search_hit_uses_source_fields():
    hit = {
        "_id": "fallback-id",
        "_score": 1.23,
        "_source": {
            "id": "docs_2",
            "text": "Elasticsearch stores searchable JSON documents.",
            "source": "docs.txt",
            "chunk_index": 2,
        },
    }

    normalized = normalize_search_hit(hit)

    assert normalized == {
        "id": "docs_2",
        "text": "Elasticsearch stores searchable JSON documents.",
        "source": "docs.txt",
        "chunk_index": 2,
        "score": 1.23,
    }


def test_normalize_search_hit_falls_back_to_hit_id():
    hit = {
        "_id": "docs_3",
        "_score": 0.42,
        "_source": {
            "text": "Fallback ids should still work.",
            "source": "docs.txt",
            "chunk_index": 3,
        },
    }

    normalized = normalize_search_hit(hit)

    assert normalized["id"] == "docs_3"


def test_search_chunks_validates_top_k():
    class FakeClient:
        def search(self, **kwargs):
            return kwargs

    with pytest.raises(ValueError, match="greater than 0"):
        search_chunks(FakeClient(), "rag-docs", "rag", top_k=0)


def test_search_chunks_calls_elasticsearch_with_expected_query():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def search(self, **kwargs):
            self.calls.append(kwargs)
            return {
                "hits": {
                    "hits": [
                        {
                            "_id": "docs_0",
                            "_score": 2.5,
                            "_source": {
                                "id": "docs_0",
                                "text": "RAG retrieves context before generation.",
                                "source": "docs.txt",
                                "chunk_index": 0,
                            },
                        }
                    ]
                }
            }

    client = FakeClient()

    results = search_chunks(
        client,
        index_name="rag-docs",
        query="What is RAG?",
        top_k=3,
    )

    assert client.calls == [
        {
            "index": "rag-docs",
            "size": 3,
            "query": {
                "match": {
                    "text": {
                        "query": "What is RAG?",
                    }
                }
            },
        }
    ]
    assert results[0]["id"] == "docs_0"
    assert results[0]["score"] == 2.5


def test_search_chunks_passes_source_filters_to_elasticsearch():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def search(self, **kwargs):
            self.calls.append(kwargs)
            return {"hits": {"hits": []}}

    client = FakeClient()

    search_chunks(
        client,
        index_name="rag-docs",
        query="What changed?",
        top_k=2,
        sources=["release-notes.txt", "playbook.txt"],
    )

    assert client.calls[0]["query"]["bool"]["filter"][0]["terms"]["source"] == [
        "release-notes.txt",
        "playbook.txt",
    ]


def test_list_index_sources_returns_sorted_source_names():
    class FakeClient:
        def search(self, **kwargs):
            return {
                "aggregations": {
                    "sources": {
                        "buckets": [
                            {"key": "docs.txt", "doc_count": 2},
                            {"key": "faq.txt", "doc_count": 1},
                        ]
                    }
                }
            }

    sources = list_index_sources(FakeClient(), index_name="rag-docs")

    assert sources == ["docs.txt", "faq.txt"]


def test_list_index_sources_validates_size():
    class FakeClient:
        def search(self, **kwargs):
            return {}

    with pytest.raises(ValueError, match="greater than 0"):
        list_index_sources(FakeClient(), index_name="rag-docs", size=0)
