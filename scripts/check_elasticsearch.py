from __future__ import annotations

from app.config import ElasticsearchSettings
from app.elasticsearch_client import create_elasticsearch_client


def main() -> int:
    try:
        settings = ElasticsearchSettings.from_env()
        client = create_elasticsearch_client(settings)
        info = client.info()
    except Exception as exc:
        print(f"Elasticsearch connection failed: {exc}")
        return 1

    cluster_name = info.get("cluster_name", "unknown")
    version = info.get("version", {}).get("number", "unknown")

    print(f"Connected to Elasticsearch cluster '{cluster_name}' (version {version})")
    print(f"Target: {settings.target()}")
    print(f"Default index: {settings.index_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
