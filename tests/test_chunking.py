import pytest
from ingestion.chunk_docs import chunk_text, load_and_chunk


def test_chunk_text_basic():
    text = 'A' * 1000
    chunks = chunk_text(text, size=300, overlap=0)
    assert len(chunks) == 4
    assert all(len(c) <= 300 for c in chunks)


def test_chunk_text_overlap():
    text = 'Hello world this is a test of chunking with overlap'
    chunks = chunk_text(text, size=20, overlap=5)
    assert len(chunks) > 1


def test_chunk_ids_are_unique():
    chunks = load_and_chunk('data/docs.txt')
    ids = [c['id'] for c in chunks]
    assert len(ids) == len(set(ids))


def test_no_empty_chunks():
    chunks = load_and_chunk('data/docs.txt')
    assert all(c['text'].strip() for c in chunks)
