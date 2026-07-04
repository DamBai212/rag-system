import pytest
from fastapi import HTTPException

from app.config import RateLimitSettings
from app.rate_limit import InMemoryRateLimiter, build_rate_limit_key


def test_rate_limit_settings_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
    monkeypatch.delenv("RATE_LIMIT_MAX_REQUESTS", raising=False)
    monkeypatch.delenv("RATE_LIMIT_WINDOW_SECONDS", raising=False)

    settings = RateLimitSettings.from_env()

    assert settings.enabled is True
    assert settings.max_requests == 20
    assert settings.window_seconds == 60


def test_rate_limiter_blocks_after_threshold():
    limiter = InMemoryRateLimiter(
        RateLimitSettings(enabled=True, max_requests=2, window_seconds=60)
    )

    limiter.check("ask:client", now=0)
    limiter.check("ask:client", now=1)

    with pytest.raises(HTTPException) as exc_info:
        limiter.check("ask:client", now=2)

    assert exc_info.value.status_code == 429


def test_rate_limiter_expires_old_requests():
    limiter = InMemoryRateLimiter(
        RateLimitSettings(enabled=True, max_requests=2, window_seconds=10)
    )

    limiter.check("ask:client", now=0)
    limiter.check("ask:client", now=1)
    limiter.check("ask:client", now=12)


def test_build_rate_limit_key_prefers_session_token():
    key = build_rate_limit_key("127.0.0.1", "/ask", session_token="session-1")

    assert key == "/ask:session-1"
