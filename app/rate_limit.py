from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from fastapi import HTTPException

from app.config import RateLimitSettings


@dataclass
class InMemoryRateLimiter:
    settings: RateLimitSettings
    buckets: dict[str, deque[float]] = field(default_factory=dict)

    def check(self, key: str, now: float | None = None) -> None:
        if not self.settings.enabled:
            return

        current_time = now if now is not None else time.time()
        window_start = current_time - self.settings.window_seconds
        bucket = self.buckets.setdefault(key, deque())

        while bucket and bucket[0] <= window_start:
            bucket.popleft()

        if len(bucket) >= self.settings.max_requests:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Rate limit exceeded. "
                    f"Try again in {self.settings.window_seconds} seconds."
                ),
            )

        bucket.append(current_time)


def build_rate_limit_key(
    client_host: str | None,
    request_path: str,
    session_token: str | None = None,
) -> str:
    identity = session_token or client_host or "unknown"
    return f"{request_path}:{identity}"
