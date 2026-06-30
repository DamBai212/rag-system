from __future__ import annotations

import argparse

from app.config import ElasticsearchSettings
from app.elasticsearch_client import create_elasticsearch_client
from app.retrieval import search_chunks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search indexed chunks in Elasticsearch."
    )
    parser.add_argument("query", help="The user query to search for.")
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum number of chunks to return.",
    )
    parser.add_argument(
        "--index",
        default=None,
        help="Override the Elasticsearch index name from the environment.",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Filter retrieval to a specific source. Repeat to include multiple sources.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        settings = ElasticsearchSettings.from_env()
        index_name = args.index or settings.index_name
        client = create_elasticsearch_client(settings)
        results = search_chunks(
            client,
            index_name=index_name,
            query=args.query,
            top_k=args.top_k,
            sources=args.source,
        )
    except Exception as exc:
        print(f"Chunk search failed: {exc}")
        return 1

    if not results:
        print(f"No chunks found for query: {args.query}")
        return 0

    print(f"Top {len(results)} result(s) from '{index_name}':")
    for index, result in enumerate(results, start=1):
        score = result["score"]
        score_text = f"{score:.3f}" if isinstance(score, (int, float)) else "n/a"
        print(f"\n[{index}] id={result['id']} score={score_text}")
        print(f"source={result['source']} chunk_index={result['chunk_index']}")
        print(result["text"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
