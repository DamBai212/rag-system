from app.config import ApiSettings, ElasticsearchSettings, OpenAISettings
from app.readiness import build_readiness_report


def test_build_readiness_report_returns_ready_when_checks_pass():
    report = build_readiness_report(
        elasticsearch_settings_loader=lambda: ElasticsearchSettings(
            cloud_id=None,
            endpoint="http://localhost:9200",
            api_key="secret-api-key",
            username=None,
            password=None,
        ),
        elasticsearch_ping=lambda settings: True,
        openai_settings_loader=lambda: OpenAISettings(api_key="test-api-key"),
        openai_client_factory=lambda settings: object(),
        api_settings_loader=lambda: ApiSettings(api_token="secret-token"),
    )

    assert report["status"] == "ready"
    assert report["checks"]["elasticsearch"]["status"] == "ok"
    assert report["checks"]["openai"]["status"] == "ok"
    assert report["checks"]["auth"]["detail"] == "Bearer token auth is configured."


def test_build_readiness_report_returns_degraded_when_checks_fail():
    report = build_readiness_report(
        elasticsearch_settings_loader=lambda: ElasticsearchSettings(
            cloud_id=None,
            endpoint="http://localhost:9200",
            api_key="secret-api-key",
            username=None,
            password=None,
        ),
        elasticsearch_ping=lambda settings: False,
        openai_settings_loader=lambda: OpenAISettings(api_key="test-api-key"),
        openai_client_factory=lambda settings: object(),
        api_settings_loader=lambda: ApiSettings(
            api_token=None,
            session_username="ops",
            session_password_hash="hashed-password",
        ),
    )

    assert report["status"] == "degraded"
    assert report["checks"]["elasticsearch"]["status"] == "error"
    assert report["checks"]["elasticsearch"]["detail"] == "Elasticsearch ping failed."
    assert (
        report["checks"]["auth"]["detail"]
        == "Dedicated browser session auth is configured."
    )
