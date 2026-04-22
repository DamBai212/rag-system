from __future__ import annotations

from typing import Callable

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import ElasticsearchSettings, OpenAISettings
from app.elasticsearch_client import create_elasticsearch_client
from app.openai_client import create_openai_client
from app.pipeline import NoRetrievedChunksError, run_rag_pipeline


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


def create_app(
    rag_runner: Callable[..., dict[str, object]] | None = None,
) -> FastAPI:
    app = FastAPI(title="RAG System API", version="0.1.0")
    app.state.rag_runner = rag_runner or build_env_rag_runner()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
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
