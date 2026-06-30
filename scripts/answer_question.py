from __future__ import annotations

import argparse

from app.config import ElasticsearchSettings, OpenAISettings
from app.elasticsearch_client import create_elasticsearch_client
from app.openai_client import create_openai_client
from app.pipeline import NoRetrievedChunksError, run_rag_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrieve chunks from Elasticsearch and generate a grounded answer."
    )
    parser.add_argument("question", help="The user question to answer.")
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Maximum number of chunks to retrieve before calling OpenAI.",
    )
    parser.add_argument(
        "--index",
        default=None,
        help="Override the Elasticsearch index name from the environment.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the OpenAI model from the environment.",
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
        elastic_settings = ElasticsearchSettings.from_env()
        openai_settings = OpenAISettings.from_env()
        index_name = args.index or elastic_settings.index_name
        model_name = args.model or openai_settings.model

        elastic_client = create_elasticsearch_client(elastic_settings)
        openai_client = create_openai_client(openai_settings)
        result = run_rag_pipeline(
            elastic_client,
            openai_client,
            question=args.question,
            index_name=index_name,
            model=model_name,
            top_k=args.top_k,
            sources=args.source,
            max_output_tokens=openai_settings.max_output_tokens,
        )
    except NoRetrievedChunksError as exc:
        print(str(exc))
        return 1
    except Exception as exc:
        print(f"RAG answer generation failed: {exc}")
        return 1

    print("Answer:\n")
    print(result["answer"])
    print("\nSources:")
    for source in result["sources"]:
        score = source["score"]
        score_text = f"{score:.3f}" if isinstance(score, (int, float)) else "n/a"
        print(
            f"- id={source['id']} source={source['source']} "
            f"chunk_index={source['chunk_index']} score={score_text}"
        )

    response_id = result["response_id"]
    if response_id:
        print(f"\nOpenAI response id: {response_id}")

    print(f"Model: {result['model']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
