from __future__ import annotations

import hashlib
import hmac
import os

PASSWORD_HASH_SCHEME = "pbkdf2_sha256"
DEFAULT_PASSWORD_HASH_ITERATIONS = 390000


def hash_password(
    password: str,
    *,
    salt_hex: str | None = None,
    iterations: int = DEFAULT_PASSWORD_HASH_ITERATIONS,
) -> str:
    if not password:
        raise ValueError("Password must not be empty.")
    if iterations <= 0:
        raise ValueError("Password hash iterations must be greater than 0.")

    salt = bytes.fromhex(salt_hex) if salt_hex is not None else os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return f"{PASSWORD_HASH_SCHEME}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash or not password:
        return False

    try:
        scheme, iterations_raw, salt_hex, digest_hex = password_hash.split("$", 3)
        iterations = int(iterations_raw)
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)
    except (AttributeError, ValueError):
        return False

    if scheme != PASSWORD_HASH_SCHEME or iterations <= 0:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_digest, expected_digest)
