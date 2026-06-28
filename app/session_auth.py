from __future__ import annotations

import hashlib
import hmac
import time

from app.config import ApiSettings
from app.password_auth import verify_password

SESSION_VERSION = "v1"


def _sign_session(expiry_timestamp: int, api_settings: ApiSettings) -> str:
    secret = api_settings.session_signing_secret()
    if not secret:
        raise ValueError("Session signing secret is not configured.")

    payload = f"{SESSION_VERSION}.{expiry_timestamp}".encode("utf-8")
    key = hashlib.sha256(secret.encode("utf-8")).digest()
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def create_signed_session_value(
    api_settings: ApiSettings,
    now: int | None = None,
) -> str:
    issued_at = now if now is not None else int(time.time())
    expiry_timestamp = issued_at + api_settings.session_ttl_seconds
    signature = _sign_session(expiry_timestamp, api_settings)
    return f"{SESSION_VERSION}.{expiry_timestamp}.{signature}"


def verify_signed_session_value(
    session_value: str | None,
    api_settings: ApiSettings,
    now: int | None = None,
) -> bool:
    if not api_settings.request_auth_enabled() or not session_value:
        return False

    try:
        version, expiry_raw, signature = session_value.split(".", 2)
        expiry_timestamp = int(expiry_raw)
    except (AttributeError, ValueError):
        return False

    if version != SESSION_VERSION:
        return False

    current_time = now if now is not None else int(time.time())
    if expiry_timestamp < current_time:
        return False

    expected_signature = _sign_session(expiry_timestamp, api_settings)
    return hmac.compare_digest(signature, expected_signature)


def verify_session_credentials(
    username: str | None,
    password: str | None,
    api_settings: ApiSettings,
) -> bool:
    if not api_settings.session_auth_enabled():
        return False
    if username != api_settings.session_username:
        return False
    return verify_password(password or "", api_settings.session_password_hash)
