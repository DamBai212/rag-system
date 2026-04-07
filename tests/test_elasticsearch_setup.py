import sys
import types

import pytest

from app.config import ElasticsearchSettings
from app.elasticsearch_client import create_elasticsearch_client


ELASTIC_ENV_VARS = [
    "ELASTIC_CLOUD_ID",
    "ELASTIC_ENDPOINT",
    "ELASTIC_API_KEY",
    "ELASTIC_USERNAME",
    "ELASTIC_PASSWORD",
    "ELASTIC_INDEX",
    "ELASTIC_VERIFY_CERTS",
    "ELASTIC_REQUEST_TIMEOUT",
]


def clear_elastic_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ELASTIC_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_settings_from_env_supports_api_key(monkeypatch: pytest.MonkeyPatch):
    clear_elastic_env(monkeypatch)
    monkeypatch.setenv("ELASTIC_ENDPOINT", "http://localhost:9200")
    monkeypatch.setenv("ELASTIC_API_KEY", "secret-api-key")

    settings = ElasticsearchSettings.from_env()

    assert settings.endpoint == "http://localhost:9200"
    assert settings.index_name == "rag-docs"
    assert settings.client_options()["hosts"] == ["http://localhost:9200"]
    assert settings.client_options()["api_key"] == "secret-api-key"


def test_settings_from_env_supports_cloud_id(monkeypatch: pytest.MonkeyPatch):
    clear_elastic_env(monkeypatch)
    monkeypatch.setenv("ELASTIC_CLOUD_ID", "deployment-name:ZXUt...")
    monkeypatch.setenv("ELASTIC_API_KEY", "secret-api-key")
    monkeypatch.setenv("ELASTIC_VERIFY_CERTS", "false")
    monkeypatch.setenv("ELASTIC_INDEX", "docs-index")

    settings = ElasticsearchSettings.from_env()
    client_options = settings.client_options()

    assert client_options["cloud_id"] == "deployment-name:ZXUt..."
    assert "hosts" not in client_options
    assert settings.verify_certs is False
    assert settings.index_name == "docs-index"


def test_settings_from_env_supports_basic_auth(monkeypatch: pytest.MonkeyPatch):
    clear_elastic_env(monkeypatch)
    monkeypatch.setenv("ELASTIC_ENDPOINT", "http://localhost:9200")
    monkeypatch.setenv("ELASTIC_USERNAME", "elastic")
    monkeypatch.setenv("ELASTIC_PASSWORD", "changeme")

    settings = ElasticsearchSettings.from_env()

    assert settings.client_options()["basic_auth"] == ("elastic", "changeme")


def test_settings_from_env_requires_target(monkeypatch: pytest.MonkeyPatch):
    clear_elastic_env(monkeypatch)
    monkeypatch.setenv("ELASTIC_API_KEY", "secret-api-key")

    with pytest.raises(
        ValueError, match="ELASTIC_CLOUD_ID or ELASTIC_ENDPOINT"
    ):
        ElasticsearchSettings.from_env()


def test_settings_from_env_requires_auth(monkeypatch: pytest.MonkeyPatch):
    clear_elastic_env(monkeypatch)
    monkeypatch.setenv("ELASTIC_ENDPOINT", "http://localhost:9200")

    with pytest.raises(
        ValueError,
        match="ELASTIC_API_KEY or both ELASTIC_USERNAME and ELASTIC_PASSWORD",
    ):
        ElasticsearchSettings.from_env()


def test_settings_from_env_validates_timeout(monkeypatch: pytest.MonkeyPatch):
    clear_elastic_env(monkeypatch)
    monkeypatch.setenv("ELASTIC_ENDPOINT", "http://localhost:9200")
    monkeypatch.setenv("ELASTIC_API_KEY", "secret-api-key")
    monkeypatch.setenv("ELASTIC_REQUEST_TIMEOUT", "0")

    with pytest.raises(ValueError, match="greater than 0"):
        ElasticsearchSettings.from_env()


def test_settings_from_env_validates_boolean(monkeypatch: pytest.MonkeyPatch):
    clear_elastic_env(monkeypatch)
    monkeypatch.setenv("ELASTIC_ENDPOINT", "http://localhost:9200")
    monkeypatch.setenv("ELASTIC_API_KEY", "secret-api-key")
    monkeypatch.setenv("ELASTIC_VERIFY_CERTS", "sometimes")

    with pytest.raises(ValueError, match="Invalid boolean value"):
        ElasticsearchSettings.from_env()


def test_create_elasticsearch_client_uses_settings(monkeypatch: pytest.MonkeyPatch):
    class FakeElasticsearch:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setitem(
        sys.modules,
        "elasticsearch",
        types.SimpleNamespace(Elasticsearch=FakeElasticsearch),
    )

    settings = ElasticsearchSettings(
        cloud_id=None,
        endpoint="http://localhost:9200",
        api_key="secret-api-key",
        username=None,
        password=None,
    )

    client = create_elasticsearch_client(settings)

    assert client.kwargs["hosts"] == ["http://localhost:9200"]
    assert client.kwargs["api_key"] == "secret-api-key"
    assert client.kwargs["request_timeout"] == 30
