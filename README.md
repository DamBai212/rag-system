# RAG System

This repository is the foundation of a Retrieval-Augmented Generation (RAG) system: it chunks source documents, validates Elasticsearch configuration, creates an index, bulk-loads searchable chunks, retrieves the most relevant context for a user query, generates a grounded answer with OpenAI, and now exposes that flow through a FastAPI endpoint.

Today, the codebase implements the ingestion, indexing, retrieval, answer-generation, and API layers. The next natural steps are deployment, authentication, and an end-user interface.

## Problem Statement

Teams often store critical knowledge across scattered documents, runbooks, support notes, and internal guides. That creates three recurring problems:

- finding the right answer takes too long
- knowledge lives in people rather than systems
- LLMs used without retrieval can sound confident while being wrong

A RAG architecture solves this by retrieving relevant internal content first and only then asking an LLM to generate an answer grounded in that context.

## What This Repo Implements Today

- document chunking from local text sources
- structured chunk metadata (`id`, `text`, `source`, `chunk_index`)
- Elasticsearch connection configuration via environment variables
- index creation with strict mappings
- bulk indexing into Elasticsearch
- retrieval of top matching chunks from Elasticsearch
- grounded answer generation with OpenAI
- FastAPI application boundary for the full RAG flow
- tests for chunking, indexing, retrieval, generation, pipeline, API, and client setup

## Architecture

### Current implemented flow

```text
source documents
    |
    v
ingestion/chunk_docs.py
    |
    v
data/chunks.json
    |
    v
scripts/check_elasticsearch.py
scripts/index_chunks.py
    |
    v
Elasticsearch index (rag-docs)
    |
    v
scripts/search_chunks.py
    |
    v
retrieved context snippets
    |
    v
scripts/answer_question.py
    |
    v
grounded answer with source references
    |
    v
FastAPI /ask endpoint
```

### Target end-to-end architecture

```text
Internal documents / SOPs / FAQs / runbooks
                  |
                  v
        Chunking + metadata enrichment
                  |
                  v
         Elasticsearch / vector-capable search
                  |
         user question arrives via API or UI
                  |
                  v
          retrieve the most relevant chunks
                  |
                  v
      send question + retrieved context to LLM
                  |
                  v
 grounded answer with traceable source references
```

### Key components

- `ingestion/chunk_docs.py`: splits documents into overlapping chunks and assigns stable metadata
- `app/config.py`: centralizes Elasticsearch environment parsing and validation
- `app/elasticsearch_client.py`: creates the Elasticsearch client
- `app/indexing.py`: builds index mappings and bulk indexing actions
- `app/openai_client.py`: creates the OpenAI client
- `app/retrieval.py`: builds search queries and normalizes retrieved hits
- `app/generation.py`: formats retrieved context and calls OpenAI for grounded answers
- `app/pipeline.py`: orchestrates retrieval plus generation for shared CLI/API usage
- `app/api.py`: exposes the full RAG flow through FastAPI
- `scripts/check_elasticsearch.py`: verifies cluster connectivity
- `scripts/index_chunks.py`: creates the index if needed and loads chunk data
- `scripts/search_chunks.py`: searches indexed chunks from the terminal
- `scripts/answer_question.py`: retrieves chunks and generates a grounded answer

## Setup Instructions

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Set one connection target:

- `ELASTIC_CLOUD_ID` for Elastic Cloud
- `ELASTIC_ENDPOINT` for a local or self-managed Elasticsearch cluster

Set one authentication method:

- `ELASTIC_API_KEY`
- or both `ELASTIC_USERNAME` and `ELASTIC_PASSWORD`

Optional settings:

- `OPENAI_MODEL` defaults to `gpt-4o-mini`
- `OPENAI_MAX_OUTPUT_TOKENS` defaults to `400`
- `ELASTIC_INDEX` defaults to `rag-docs`
- `ELASTIC_VERIFY_CERTS` defaults to `true`
- `ELASTIC_REQUEST_TIMEOUT` defaults to `30`

### 4. Generate chunks from the sample document

```bash
python ingestion/chunk_docs.py
```

This creates `data/chunks.json` from `data/docs.txt`.

### 5. Verify Elasticsearch connectivity

```bash
python scripts/check_elasticsearch.py
```

### 6. Index the chunks

```bash
python scripts/index_chunks.py
```

To override the default input file or index name:

```bash
python scripts/index_chunks.py --input data/chunks.json --index rag-docs
```

### 7. Search indexed chunks

```bash
python scripts/search_chunks.py "What is Retrieval-Augmented Generation?" --top-k 3
```

### 8. Generate a grounded answer

```bash
python scripts/answer_question.py "How does RAG reduce hallucinations?" --top-k 3
```

### 9. Run tests

```bash
PYTHONPATH=. pytest
```

### 10. Run the API locally

```bash
uvicorn app.api:app --reload
```

Example request:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"How does RAG reduce hallucinations?","top_k":3}'
```

## Concrete Use Case Example

Imagine an internal knowledge assistant for a support team.

1. Product guides, troubleshooting notes, and runbooks are ingested and chunked.
2. Those chunks are indexed in Elasticsearch with source metadata.
3. A support agent asks: "How do I check whether Elasticsearch is configured correctly?"
4. The retrieval layer finds the most relevant chunks covering connection targets, authentication, and timeouts.
5. The generation layer sends the question plus retrieved context to OpenAI.
6. The LLM returns a concise answer grounded in that context, reducing guesswork and making the answer easier to trust.

That is the core value of this architecture: faster answers, less dependence on tribal knowledge, and more consistent support decisions.

## Transreport Use Case

For Transreport, this same architecture could power an internal knowledge assistant for Ops and Support teams.

The assistant could index materials such as:

- operational playbooks
- support macros and troubleshooting guides
- escalation paths
- incident retrospectives
- release notes
- partner-specific processes and internal FAQs

In practice, that means an Ops or Support teammate could ask questions like:

- "What is the escalation path for this issue type?"
- "Has this problem happened before, and what was the resolution?"
- "What changed in the latest release that might explain this behaviour?"
- "Which internal process should I follow for this partner scenario?"

Commercially, this matters because it can:

- reduce average handling time for internal and customer-facing support work
- shorten ramp-up time for new team members
- make service decisions more consistent across shifts and teams
- reduce interruptions to senior staff who currently act as the memory layer
- turn internal documentation into an operational asset instead of a static archive

For a company scaling Ops and Support, that is more than a technical improvement. It is a way to improve speed, quality, and knowledge reuse without linearly increasing headcount.

## Current Status

The repository currently covers the ingestion, indexing, retrieval, grounded answer-generation, and API foundation of a RAG system. The next logical steps are:

- deployment of the full workflow behind an application boundary
- authentication, observability, and UI polish for end users
