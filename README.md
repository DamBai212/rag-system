# RAG System

A production-style Retrieval-Augmented Generation system built 
on AWS, Elasticsearch, and OpenAI.

## Status
🚧 In progress — following a 14-day build curriculum

## Stack
- Python + FastAPI
- Elastic Cloud (Elasticsearch)
- OpenAI (gpt-4o-mini)
- AWS Lambda + API Gateway
- Terraform

## Progress
- [x] Day 1 — Project setup
- [x] Day 2 — Document ingestion + chunking
- [x] Day 3 — Elasticsearch setup
- [x] Day 4 — Index documents
- [ ] Day 5 — Retrieval function
- [ ] Day 6 — LLM integration
- [ ] Day 7 — Full RAG pipeline

## Elasticsearch Setup

The project now includes a reusable Elasticsearch configuration layer for either
Elastic Cloud or a direct endpoint, plus a quick connectivity check script.

1. Install the current project dependencies with `pip install -r requirements.txt`
2. Populate your local environment from `.env.example`
3. Run `python scripts/check_elasticsearch.py` to verify the connection

Use `ELASTIC_CLOUD_ID` for Elastic Cloud, or `ELASTIC_ENDPOINT` for a local or
self-managed cluster. Authentication can be provided with an API key or with
`ELASTIC_USERNAME` and `ELASTIC_PASSWORD`.

## Index Documents

Once `data/chunks.json` exists and your Elasticsearch environment variables are
set, index the chunks with:

`python scripts/index_chunks.py`

You can override the defaults if needed:

`python scripts/index_chunks.py --input data/chunks.json --index rag-docs`
