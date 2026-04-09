from __future__ import annotations

import argparse

from app.config import ElasticsearchSettings
from app.elasticsearch_client import create_elasticsearch_client
from app.indexing import bulk_index_chunks, ensure_index, load_chunks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Index chunked documents into Elasticsearch."
    )
    parser.add_argument(
        "--input",
        default="data/chunks.json",
        help="Path to the chunk JSON file.",
    )
    parser.add_argument(
        "--index",
        default=None,
        help="Override the Elasticsearch index name from the environment.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        settings = ElasticsearchSettings.from_env()
        index_name = args.index or settings.index_name
        client = create_elasticsearch_client(settings)
        chunks = load_chunks(args.input)
        created = ensure_index(client, index_name=index_name)
        indexed_count, errors = bulk_index_chunks(
            client,
            index_name=index_name,
            chunks=chunks,
        )
    except Exception as exc:
        print(f"Chunk indexing failed: {exc}")
        return 1

    if created:
        print(f"Created Elasticsearch index '{index_name}'")
    else:
        print(f"Using existing Elasticsearch index '{index_name}'")

    print(f"Indexed {indexed_count} chunks from {args.input}")

    if errors:
        print(f"Encountered {len(errors)} indexing error(s)")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
