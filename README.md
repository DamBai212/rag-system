# RAG System

This repository is the foundation of a Retrieval-Augmented Generation (RAG) system: it chunks source documents, validates Elasticsearch configuration, creates an index, and bulk-loads searchable chunks that can later power a grounded AI assistant.

Today, the codebase implements the ingestion and indexing layer. The retrieval API, prompt orchestration, and answer generation layers are the natural next steps.

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
- tests for chunking, indexing, and Elasticsearch setup

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
- `scripts/check_elasticsearch.py`: verifies cluster connectivity
- `scripts/index_chunks.py`: creates the index if needed and loads chunk data

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

- `ELASTIC_INDEX` defaults to `rag-docs`
- `ELASTIC_VERIFY_CERTS` defaults to `true`
- `ELASTIC_REQUEST_TIMEOUT` defaults to `30`
- `OPENAI_API_KEY` can be added now for the future generation layer, although it is not used by the current code yet

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

### 7. Run tests

```bash
PYTHONPATH=. pytest
```

## Concrete Use Case Example

Imagine an internal knowledge assistant for a support team.

1. Product guides, troubleshooting notes, and runbooks are ingested and chunked.
2. Those chunks are indexed in Elasticsearch with source metadata.
3. A support agent asks: "How do I check whether Elasticsearch is configured correctly?"
4. The retrieval layer finds the most relevant chunks covering connection targets, authentication, and timeouts.
5. The LLM generates a concise answer using only the retrieved context, reducing guesswork and making the answer easier to trust.

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

The repository currently covers the ingestion and indexing foundation of a RAG system. The next logical steps are:

- retrieval from Elasticsearch
- prompt assembly with retrieved context
- OpenAI response generation
- an internal API or UI for end users
