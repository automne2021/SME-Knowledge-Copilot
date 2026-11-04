"""Non-streaming, standalone P0 answering; no oracle/history context input."""

from fastapi import APIRouter, Request

from app.api.search import runtime_for_app
from app.core.config import get_settings
from app.core.db import DbSession
from app.core.errors import success
from app.core.security import CurrentUser
from app.schemas.answer import ChatQuery
from app.services.chat import query
from app.services.gemini import GeminiProvider

router = APIRouter(tags=["chat"])


@router.post("/chat/query")
def chat_query(payload: ChatQuery, db: DbSession, user: CurrentUser, request: Request):
    provider_factory = getattr(request.app.state, "provider_factory", GeminiProvider)
    return success(
        request,
        query(
            db,
            user,
            payload,
            get_settings(),
            lambda: runtime_for_app(request),
            provider_factory,
            request.app.state.llm_capacity,
        ),
    )
