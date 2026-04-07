from __future__ import annotations

from app.config import ElasticsearchSettings


def create_elasticsearch_client(
    settings: ElasticsearchSettings | None = None,
):
    settings = settings or ElasticsearchSettings.from_env()

    try:
        from elasticsearch import Elasticsearch
    except ImportError as exc:
        raise RuntimeError(
            "The `elasticsearch` package is not installed. "
            "Install the project dependencies before connecting."
        ) from exc

    return Elasticsearch(**settings.client_options())


def ping_elasticsearch(settings: ElasticsearchSettings | None = None) -> bool:
    client = create_elasticsearch_client(settings=settings)
    return bool(client.ping())
