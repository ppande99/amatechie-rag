import uuid
from functools import lru_cache

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat import ChatModel, make_chat
from app.config import settings
from app.db import get_session
from app.ingestion.embedder import Embedder, make_embedder
from app.rag.answer import answer_question

router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class CitationOut(BaseModel):
    n: int
    source: str
    chunk_id: str
    snippet: str


class AskResponse(BaseModel):
    answer: str
    refused: bool
    reason: str | None
    citations: list[CitationOut]
    trace_id: str


@lru_cache
def get_embedder() -> Embedder:
    return make_embedder(settings.embedder_kind)


@lru_cache
def get_chat() -> ChatModel:
    return make_chat(settings.chat_kind)


@router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    # DEV ONLY: identity comes from headers. Real authentication replaces this before any public
    # deployment; never trust client-supplied tenant or groups on a public endpoint.
    x_tenant_id: str = Header(default="demo"),
    x_user_groups: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
    embedder: Embedder = Depends(get_embedder),
    chat: ChatModel = Depends(get_chat),
) -> AskResponse:
    groups = [g.strip() for g in x_user_groups.split(",") if g.strip()]
    result = await answer_question(
        session,
        question=body.question,
        tenant_id=x_tenant_id,
        user_groups=groups,
        embedder=embedder,
        chat=chat,
    )
    return AskResponse(
        answer=result.text,
        refused=result.refused,
        reason=result.reason,
        citations=[CitationOut(**c.__dict__) for c in result.citations],
        trace_id=str(uuid.uuid4()),
    )
