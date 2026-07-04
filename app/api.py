from __future__ import annotations

from typing import Callable

from fastapi import Cookie, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.config import (
    ApiSettings,
    ElasticsearchSettings,
    ObservabilitySettings,
    OpenAISettings,
    RateLimitSettings,
)
from app.elasticsearch_client import create_elasticsearch_client
from app.observability import add_observability_middleware
from app.openai_client import create_openai_client
from app.pipeline import NoRetrievedChunksError, run_rag_pipeline
from app.rate_limit import InMemoryRateLimiter, build_rate_limit_key
from app.readiness import build_readiness_report
from app.retrieval import list_index_sources
from app.session_auth import (
    create_signed_session_value,
    verify_session_credentials,
    verify_signed_session_value,
)
from app.ui import render_chat_ui

SESSION_COOKIE_NAME = "rag_session"


class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=3, gt=0)
    sources: list[str] = Field(default_factory=list)
    index: str | None = None
    model: str | None = None


class SourceReference(BaseModel):
    id: str | None
    source: str | None
    chunk_index: int | None
    score: float | None
    excerpt: str | None = None


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceReference]
    model: str
    response_id: str | None
    retrieved_chunk_count: int


class SessionRequest(BaseModel):
    token: str | None = None
    username: str | None = None
    password: str | None = None


class SessionResponse(BaseModel):
    auth_enabled: bool
    authenticated: bool
    session_login_enabled: bool
    token_login_enabled: bool


class ReadinessCheck(BaseModel):
    status: str
    detail: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, ReadinessCheck]


class SourceCatalogResponse(BaseModel):
    sources: list[str]


def build_env_rag_runner() -> Callable[..., dict[str, object]]:
    def rag_runner(
        *,
        question: str,
        top_k: int = 3,
        sources: list[str] | None = None,
        index: str | None = None,
        model: str | None = None,
    ) -> dict[str, object]:
        elastic_settings = ElasticsearchSettings.from_env()
        openai_settings = OpenAISettings.from_env()
        elastic_client = create_elasticsearch_client(elastic_settings)
        openai_client = create_openai_client(openai_settings)

        return run_rag_pipeline(
            elastic_client,
            openai_client,
            question=question,
            index_name=index or elastic_settings.index_name,
            model=model or openai_settings.model,
            top_k=top_k,
            sources=sources,
            max_output_tokens=openai_settings.max_output_tokens,
        )

    return rag_runner


def build_env_source_lister() -> Callable[..., list[str]]:
    def source_lister(
        *,
        index: str | None = None,
    ) -> list[str]:
        elastic_settings = ElasticsearchSettings.from_env()
        elastic_client = create_elasticsearch_client(elastic_settings)
        return list_index_sources(
            elastic_client,
            index_name=index or elastic_settings.index_name,
        )

    return source_lister


def build_session_response(
    api_settings: ApiSettings,
    *,
    authenticated: bool,
) -> SessionResponse:
    return SessionResponse(
        auth_enabled=api_settings.request_auth_enabled(),
        authenticated=authenticated,
        session_login_enabled=api_settings.session_auth_enabled(),
        token_login_enabled=api_settings.api_token_auth_enabled(),
    )


def require_request_auth(
    authorization: str | None,
    session_token: str | None,
    api_settings: ApiSettings,
) -> None:
    if not api_settings.request_auth_enabled():
        return

    if verify_signed_session_value(session_token, api_settings):
        return

    if authorization:
        if not api_settings.api_token_auth_enabled():
            raise HTTPException(
                status_code=401,
                detail="Bearer token auth is not enabled for this deployment.",
            )

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or token != api_settings.api_token:
            raise HTTPException(status_code=401, detail="Invalid API token.")
        return

    if api_settings.session_auth_enabled():
        raise HTTPException(status_code=401, detail="Authentication required.")

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")


def create_session_cookie(response: Response, api_settings: ApiSettings) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_signed_session_value(api_settings),
        httponly=True,
        samesite="lax",
        secure=api_settings.session_cookie_secure,
        max_age=api_settings.session_ttl_seconds,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME)


def create_app(
    rag_runner: Callable[..., dict[str, object]] | None = None,
    api_settings: ApiSettings | None = None,
    observability_settings: ObservabilitySettings | None = None,
    rate_limiter: InMemoryRateLimiter | None = None,
    readiness_checker: Callable[[], dict[str, object]] | None = None,
    source_lister: Callable[..., list[str]] | None = None,
) -> FastAPI:
    app = FastAPI(title="RAG System API", version="0.1.0")
    app.state.rag_runner = rag_runner or build_env_rag_runner()
    app.state.api_settings = api_settings or ApiSettings.from_env()
    app.state.rate_limiter = rate_limiter or InMemoryRateLimiter(
        RateLimitSettings.from_env()
    )
    app.state.readiness_checker = readiness_checker or build_readiness_report
    app.state.source_lister = source_lister or build_env_source_lister()
    add_observability_middleware(
        app,
        observability_settings or ObservabilitySettings.from_env(),
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", response_model=ReadinessResponse)
    def ready(response: Response) -> dict[str, object]:
        readiness = app.state.readiness_checker()
        if readiness["status"] != "ready":
            response.status_code = 503
        return readiness

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return render_chat_ui()

    @app.get("/sources", response_model=SourceCatalogResponse)
    def sources(
        authorization: str | None = Header(default=None),
        session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    ) -> SourceCatalogResponse:
        require_request_auth(
            authorization,
            session_token,
            app.state.api_settings,
        )
        return SourceCatalogResponse(sources=app.state.source_lister())

    @app.get("/auth/status", response_model=SessionResponse)
    def auth_status(
        session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    ) -> SessionResponse:
        return build_session_response(
            app.state.api_settings,
            authenticated=verify_signed_session_value(
                session_token,
                app.state.api_settings,
            ),
        )

    @app.post("/session", response_model=SessionResponse)
    def create_session(
        request: SessionRequest,
        response: Response,
    ) -> SessionResponse:
        if not app.state.api_settings.request_auth_enabled():
            return build_session_response(
                app.state.api_settings,
                authenticated=False,
            )

        if app.state.api_settings.session_auth_enabled():
            if not verify_session_credentials(
                request.username,
                request.password,
                app.state.api_settings,
            ):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid username or password.",
                )
        elif request.token != app.state.api_settings.api_token:
            raise HTTPException(status_code=401, detail="Invalid API token.")

        create_session_cookie(response, app.state.api_settings)
        return build_session_response(app.state.api_settings, authenticated=True)

    @app.delete("/session", response_model=SessionResponse)
    def delete_session(response: Response) -> SessionResponse:
        clear_session_cookie(response)
        return build_session_response(
            app.state.api_settings,
            authenticated=False,
        )

    @app.post("/ask", response_model=AskResponse)
    def ask(
        fastapi_request: Request,
        request: AskRequest,
        authorization: str | None = Header(default=None),
        session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    ) -> AskResponse:
        require_request_auth(
            authorization,
            session_token,
            app.state.api_settings,
        )
        app.state.rate_limiter.check(
            build_rate_limit_key(
                client_host=fastapi_request.client.host if fastapi_request.client else None,
                request_path=fastapi_request.url.path,
                session_token=session_token,
            )
        )

        try:
            result = app.state.rag_runner(
                question=request.question,
                top_k=request.top_k,
                sources=request.sources,
                index=request.index,
                model=request.model,
            )
        except NoRetrievedChunksError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"RAG pipeline failed: {exc}") from exc

        return AskResponse(**result)

    return app


app = create_app()
