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
    settings = getattr(request.app.state, "rag_settings", None)
    settings = (settings if settings is not None else get_settings()).model_copy(deep=True)
    provider_factory = getattr(request.app.state, "provider_factory", GeminiProvider)
    # Internal eval-only hook; clients cannot select/enable capture in the payload.
    capture_factory = getattr(request.app.state, "query_capture_factory", None)
    observer = capture_factory(user, payload, settings) if capture_factory is not None else None
    if observer is not None:
        provider_factory = observer.provider_factory
    try:
        result = query(
            db,
            user,
            payload,
            settings,
            lambda: runtime_for_app(request),
            provider_factory,
            request.app.state.llm_capacity,
            observer=observer,
        )
        if observer is not None:
            observer.succeeded(result)
    except Exception as exc:
        if observer is not None:
            observer.failed(exc)
        raise
    return success(request, result)
