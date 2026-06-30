# RAG System

This repository is the foundation of a Retrieval-Augmented Generation (RAG) system: it chunks source documents, validates Elasticsearch configuration, creates an index, bulk-loads searchable chunks, retrieves the most relevant context for a user query, generates a grounded answer with OpenAI, and now exposes that flow through a FastAPI endpoint.

Today, the codebase implements the ingestion, indexing, retrieval, answer-generation, API, deployment-entrypoint, basic observability, browser UI, and production-oriented session auth layers. The next natural step is hosted deployment and deeper UX polish for real users.

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
- optional bearer-token protection for the `/ask` endpoint
- container-ready runtime entrypoint for hosted deployment
- request IDs and structured request logging for API observability
- structured readiness checks for Elasticsearch, OpenAI, and auth configuration
- source-scoped retrieval for narrowing questions to selected documents
- lightweight browser UI served directly from the FastAPI app, with local answer history, retrieval metadata, and source filtering
- browser-friendly session auth with either a shared API token or dedicated username/password credentials
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
- `app/server.py`: starts the API using environment-driven host/port settings
- `app/observability.py`: adds request IDs and structured API request logging
- `app/ui.py`: serves a lightweight browser interface for asking questions
- `POST /session`, `DELETE /session`, and `GET /auth/status`: support browser login with an HTTP-only cookie
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
- `RAG_API_TOKEN` enables bearer-token auth for `POST /ask` when set
- `SESSION_USERNAME` and `SESSION_PASSWORD_HASH` enable dedicated browser sign-in
- `SESSION_SECRET` signs browser session cookies; defaults to the session password hash or API token if omitted
- `SESSION_TTL_SECONDS` defaults to `43200` (12 hours)
- `SESSION_COOKIE_SECURE` defaults to `false`; set it to `true` behind HTTPS
- `LOG_LEVEL` defaults to `INFO`
- `RATE_LIMIT_ENABLED` defaults to `true`
- `RATE_LIMIT_MAX_REQUESTS` defaults to `20`
- `RATE_LIMIT_WINDOW_SECONDS` defaults to `60`
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

To scope retrieval to specific source documents:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What changed in the latest release?","top_k":3,"sources":["release-notes.txt"]}'
```

If `RAG_API_TOKEN` is set, include a bearer token:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{"question":"How does RAG reduce hallucinations?","top_k":3}'
```

Every API response also includes an `X-Request-ID` header. You can provide your
own `X-Request-ID` value, or let the API generate one for tracing.

Use `GET /ready` for deployment readiness. It returns `200` when Elasticsearch,
OpenAI, and auth configuration checks pass, and `503` when the app still needs
setup.

Use `GET /sources` to retrieve the distinct indexed source names available for
source-scoped querying. It follows the same auth rules as `POST /ask`.

The browser UI can also authenticate by sending either the shared API token or
dedicated session credentials to `POST /session`, which sets a signed,
expiring HTTP-only cookie used for later `POST /ask` requests.

To generate a `SESSION_PASSWORD_HASH` value:

```bash
python scripts/hash_password.py
```

The `POST /ask` endpoint is also protected by a simple in-process rate limit by
default. Tune the threshold with `RATE_LIMIT_MAX_REQUESTS` and
`RATE_LIMIT_WINDOW_SECONDS`, or disable it with `RATE_LIMIT_ENABLED=false`.

### 11. Open the browser UI

Start the API, then open `http://127.0.0.1:8000/` in a browser. The UI talks to
the same `POST /ask` endpoint and supports optional browser sign-in with either
a shared token or dedicated session credentials. You can also scope questions to
an indexed source directly from the browser.

## Deployment

### Run with the packaged entrypoint

This uses `HOST` and `PORT` environment variables and is a better fit for
deployment than the local `--reload` command:

```bash
python -m app.server
```

### Build a container image

```bash
docker build -t rag-system-api .
```

### Run the container

```bash
docker run --rm -p 8000:8000 --env-file .env rag-system-api
```

Most hosting platforms inject `PORT` automatically, and the container entrypoint
will use it without any code changes.

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

The repository currently covers the ingestion, indexing, retrieval, grounded answer-generation, API, deployment-entrypoint, basic observability, browser UI, and production-oriented session auth foundation of a RAG system. The next logical steps are:

- hosted deployment of the full workflow behind an application boundary
- richer end-user polish around the browser experience
