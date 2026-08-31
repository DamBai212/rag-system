# RAG System

[![Tests](https://github.com/DamBai212/rag-system/actions/workflows/tests.yml/badge.svg)](https://github.com/DamBai212/rag-system/actions/workflows/tests.yml)

A FastAPI + Elasticsearch service that answers questions by retrieving relevant chunks of your own documents and asking an LLM to generate a grounded, source-cited answer instead of hallucinating from parametric memory alone.

## Demo

<!-- TODO: add a screenshot or short GIF of the browser UI (ask a question, show the answer + sources) -->
_Screenshot/demo coming soon — run the app locally with the quickstart below to try it now._

## What this repo implements

- document chunking from local text sources, with stable per-chunk IDs and metadata
- Elasticsearch index creation, bulk indexing, and BM25-based retrieval (with optional source filtering)
- grounded answer generation via OpenAI, with citations back to the retrieved chunks
- a FastAPI app exposing `/ask`, `/sources`, `/ready`, `/health`, and session/token auth endpoints
- a lightweight browser UI served directly from the API, with answer history and source-scoped search
- request IDs, structured request logging, and readiness checks for deployment
- 86 tests covering chunking, indexing, retrieval, generation, auth, rate limiting, and the API layer

## Architecture

### Request flow

```text
source documents (data/docs.txt)
        |
        v
ingestion/chunk_docs.py  -->  data/chunks.json
        |
        v
scripts/index_chunks.py  -->  Elasticsearch index (rag-docs)
        |
        v
POST /ask  -->  app/retrieval.py (BM25 search, optional source filter)
        |
        v
app/generation.py  -->  OpenAI (question + retrieved context)
        |
        v
grounded answer + source excerpts
```

### Key components

| Component | Responsibility |
|---|---|
| `ingestion/chunk_docs.py` | splits raw text into overlapping, fixed-size chunks with stable IDs |
| `app/config.py` | parses and validates Elasticsearch/OpenAI/session/rate-limit settings from env vars |
| `app/indexing.py` | builds the strict index mapping and bulk-index actions |
| `app/retrieval.py` | builds Elasticsearch queries and normalizes search hits |
| `app/generation.py` | formats retrieved context and calls OpenAI for a grounded answer |
| `app/pipeline.py` | orchestrates retrieval + generation for both the CLI scripts and the API |
| `app/api.py` | FastAPI app: `/ask`, `/sources`, `/ready`, `/health`, session auth |
| `app/ui.py` | serves the browser UI |

### A real design decision: lexical search over vector search

Retrieval here uses Elasticsearch's BM25 `match` query on the chunk text, not embeddings or a vector index. That's a deliberate trade-off for this stage of the project, not an oversight:

- **No embedding pipeline to run or keep in sync.** Every chunk is searchable the moment it's indexed — no batch embedding job, no vector store, no re-embedding when the model changes.
- **Good fit for the actual queries.** Most internal-knowledge questions (support runbooks, FAQs, release notes) share vocabulary with the source documents, where BM25's term-overlap scoring already performs well. Vector search earns its complexity when queries and documents are worded very differently.
- **Debuggable.** A BM25 score and matched terms are easy to reason about when an answer looks wrong; a cosine-similarity score over an opaque embedding is not.

The trade-off: BM25 misses paraphrases and synonyms that don't share vocabulary with the source text. `app/retrieval.py` isolates query-building behind `build_chunk_search_query`, so swapping in (or adding, via hybrid search) a `dense_vector` field and a k-NN query later is a contained change, not a rewrite.

Chunking is similarly simple on purpose: `ingestion/chunk_docs.py` splits on fixed character windows with overlap rather than sentence- or section-aware splitting. It's predictable and fast, at the cost of occasionally cutting a chunk mid-sentence — an acceptable trade for a project this size, and an isolated place to improve if recall on longer documents becomes an issue.

## Quickstart

Verified from a clean clone.

### 1. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Then set, at minimum:

- `OPENAI_API_KEY`
- One Elasticsearch target: `ELASTIC_CLOUD_ID` or `ELASTIC_ENDPOINT`
- One Elasticsearch credential: `ELASTIC_API_KEY`, or both `ELASTIC_USERNAME` and `ELASTIC_PASSWORD`

See [Configuration reference](#configuration-reference) below for every optional setting.

### 3. Run the tests (no external services required)

```bash
PYTHONPATH=. pytest
```

### 4. Chunk the sample document

```bash
python ingestion/chunk_docs.py
```

Creates `data/chunks.json` from `data/docs.txt`.

### 5. Verify Elasticsearch connectivity and index the chunks

```bash
python scripts/check_elasticsearch.py
python scripts/index_chunks.py
```

### 6. Ask a question from the CLI

```bash
python scripts/answer_question.py "How does RAG reduce hallucinations?" --top-k 3
```

### 7. Run the API and browser UI

```bash
uvicorn app.api:app --reload
```

Open `http://127.0.0.1:8000/` for the browser UI, or call the API directly:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"How does RAG reduce hallucinations?","top_k":3}'
```

Scope a question to specific source documents:

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

Other useful endpoints:

- `GET /health` — liveness
- `GET /ready` — returns `200` when Elasticsearch, OpenAI, and auth config all check out, `503` otherwise
- `GET /sources` — distinct indexed source names, for source-scoped queries (same auth as `/ask`)
- `POST /session` / `DELETE /session` — browser sign-in with a shared token or dedicated username/password, backed by a signed HTTP-only cookie

To generate a `SESSION_PASSWORD_HASH` for dedicated login credentials:

```bash
python scripts/hash_password.py
```

## Configuration reference

| Variable | Default | Notes |
|---|---|---|
| `OPENAI_API_KEY` | _required_ | |
| `OPENAI_MODEL` | `gpt-4o-mini` | |
| `OPENAI_MAX_OUTPUT_TOKENS` | `400` | |
| `ELASTIC_CLOUD_ID` / `ELASTIC_ENDPOINT` | _one required_ | connection target |
| `ELASTIC_API_KEY` / (`ELASTIC_USERNAME` + `ELASTIC_PASSWORD`) | _one required_ | credentials |
| `ELASTIC_INDEX` | `rag-docs` | |
| `ELASTIC_VERIFY_CERTS` | `true` | |
| `ELASTIC_REQUEST_TIMEOUT` | `30` | seconds |
| `RAG_API_TOKEN` | unset | enables bearer-token auth for `/ask` when set |
| `SESSION_USERNAME` / `SESSION_PASSWORD_HASH` | unset | enable dedicated browser login (set both together) |
| `SESSION_SECRET` | falls back to password hash or API token | signs session cookies |
| `SESSION_TTL_SECONDS` | `43200` (12h) | |
| `SESSION_COOKIE_SECURE` | `false` | set `true` behind HTTPS |
| `LOG_LEVEL` | `INFO` | |
| `RATE_LIMIT_ENABLED` | `true` | |
| `RATE_LIMIT_MAX_REQUESTS` | `20` | per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | |

## Deployment

Run with the packaged entrypoint (reads `HOST`/`PORT`, a better fit than `--reload` for hosting):

```bash
python -m app.server
```

Or build and run the container:

```bash
docker build -t rag-system-api .
docker run --rm -p 8000:8000 --env-file .env rag-system-api
```

Most hosting platforms inject `PORT` automatically; the entrypoint picks it up without code changes.

## Testing

```bash
PYTHONPATH=. pytest
```

All 86 tests run against mocked Elasticsearch/OpenAI clients — no live credentials or network access needed. Tests run automatically on every push and pull request via [GitHub Actions](.github/workflows/tests.yml).

## Example use case

An internal knowledge base for an ops or support team — runbooks, troubleshooting guides, release notes, escalation paths — indexed and made queryable in natural language:

1. Docs are ingested, chunked, and indexed with source metadata.
2. A teammate asks: "What's the escalation path for this issue type?"
3. Retrieval finds the most relevant chunks; generation turns them into a grounded, cited answer.

The payoff is faster answers, less dependence on a few people's tribal knowledge, and more consistent responses across a team.

## Current status and next steps

Implemented: ingestion, indexing, BM25 retrieval with source filtering, grounded generation, a FastAPI service with session/token auth and rate limiting, a browser UI, readiness checks, structured logging, and a CI test suite.

Not yet implemented, and the natural next steps: hosted deployment, and (per the design-decision note above) an optional embedding-based or hybrid retrieval path for queries that don't share vocabulary with the source documents.
