from __future__ import annotations

import argparse

from app.config import ElasticsearchSettings, OpenAISettings
from app.elasticsearch_client import create_elasticsearch_client
from app.generation import generate_grounded_answer
from app.openai_client import create_openai_client
from app.retrieval import search_chunks


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
        chunks = search_chunks(
            elastic_client,
            index_name=index_name,
            query=args.question,
            top_k=args.top_k,
        )
    except Exception as exc:
        print(f"RAG answer generation failed: {exc}")
        return 1

    if not chunks:
        print(f"No retrieved chunks found for question: {args.question}")
        return 1

    try:
        result = generate_grounded_answer(
            openai_client,
            model=model_name,
            question=args.question,
            chunks=chunks,
            max_output_tokens=openai_settings.max_output_tokens,
        )
    except Exception as exc:
        print(f"OpenAI answer generation failed: {exc}")
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
