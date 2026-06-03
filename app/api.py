from __future__ import annotations

from typing import Callable

from fastapi import Cookie, FastAPI, Header, HTTPException, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.config import (
    ApiSettings,
    ElasticsearchSettings,
    ObservabilitySettings,
    OpenAISettings,
)
from app.elasticsearch_client import create_elasticsearch_client
from app.observability import add_observability_middleware
from app.openai_client import create_openai_client
from app.pipeline import NoRetrievedChunksError, run_rag_pipeline
from app.ui import render_chat_ui

SESSION_COOKIE_NAME = "rag_session"


class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=3, gt=0)
    index: str | None = None
    model: str | None = None


class SourceReference(BaseModel):
    id: str | None
    source: str | None
    chunk_index: int | None
    score: float | None


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceReference]
    model: str
    response_id: str | None
    retrieved_chunk_count: int


class SessionRequest(BaseModel):
    token: str


class SessionResponse(BaseModel):
    auth_enabled: bool
    authenticated: bool


def build_env_rag_runner() -> Callable[..., dict[str, object]]:
    def rag_runner(
        *,
        question: str,
        top_k: int = 3,
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
            max_output_tokens=openai_settings.max_output_tokens,
        )

    return rag_runner


def require_api_token(
    authorization: str | None,
    session_token: str | None,
    api_settings: ApiSettings,
) -> None:
    if not api_settings.auth_enabled():
        return

    if session_token == api_settings.api_token:
        return

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != api_settings.api_token:
        raise HTTPException(status_code=401, detail="Invalid API token.")


def create_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 12,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME)


def create_app(
    rag_runner: Callable[..., dict[str, object]] | None = None,
    api_settings: ApiSettings | None = None,
    observability_settings: ObservabilitySettings | None = None,
) -> FastAPI:
    app = FastAPI(title="RAG System API", version="0.1.0")
    app.state.rag_runner = rag_runner or build_env_rag_runner()
    app.state.api_settings = api_settings or ApiSettings.from_env()
    add_observability_middleware(
        app,
        observability_settings or ObservabilitySettings.from_env(),
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return render_chat_ui()

    @app.get("/auth/status", response_model=SessionResponse)
    def auth_status(
        session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    ) -> SessionResponse:
        auth_enabled = app.state.api_settings.auth_enabled()
        authenticated = auth_enabled and session_token == app.state.api_settings.api_token
        return SessionResponse(
            auth_enabled=auth_enabled,
            authenticated=authenticated,
        )

    @app.post("/session", response_model=SessionResponse)
    def create_session(
        request: SessionRequest,
        response: Response,
    ) -> SessionResponse:
        if not app.state.api_settings.auth_enabled():
            return SessionResponse(auth_enabled=False, authenticated=False)

        if request.token != app.state.api_settings.api_token:
            raise HTTPException(status_code=401, detail="Invalid API token.")

        create_session_cookie(response, request.token)
        return SessionResponse(auth_enabled=True, authenticated=True)

    @app.delete("/session", response_model=SessionResponse)
    def delete_session(response: Response) -> SessionResponse:
        clear_session_cookie(response)
        return SessionResponse(
            auth_enabled=app.state.api_settings.auth_enabled(),
            authenticated=False,
        )

    @app.post("/ask", response_model=AskResponse)
    def ask(
        request: AskRequest,
        authorization: str | None = Header(default=None),
        session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    ) -> AskResponse:
        require_api_token(
            authorization,
            session_token,
            app.state.api_settings,
        )

        try:
            result = app.state.rag_runner(
                question=request.question,
                top_k=request.top_k,
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
