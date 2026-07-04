from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import FastAPI, Request

from app.config import ObservabilitySettings

REQUEST_ID_HEADER = "X-Request-ID"
API_LOGGER_NAME = "rag.api"


def configure_api_logger(settings: ObservabilitySettings) -> logging.Logger:
    logger = logging.getLogger(API_LOGGER_NAME)
    logger.setLevel(settings.log_level)
    logger.propagate = True

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    return logger


def log_api_event(logger: logging.Logger, event: str, **fields: object) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, sort_keys=True, default=str))


def add_observability_middleware(
    app: FastAPI,
    settings: ObservabilitySettings,
) -> None:
    logger = configure_api_logger(settings)
    app.state.api_logger = logger
    app.state.observability_settings = settings

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            log_api_event(
                logger,
                "api_request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers[REQUEST_ID_HEADER] = request_id
        log_api_event(
            logger,
            "api_request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
