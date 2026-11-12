"""Search/source APIs; local runtime is lazy and closed by the app lifespan."""

import uuid

from fastapi import APIRouter, Request, Response

from app.core.config import get_settings
from app.core.db import DbSession
from app.core.errors import success
from app.core.security import CurrentUser
from app.schemas.search import SearchRequest
from app.services.retrieval import RetrievalRuntime, search
from app.services.sources import source_chunk, source_content

router = APIRouter(tags=["retrieval"])


def settings_for_app(request):
    settings = getattr(request.app.state, "rag_settings", None)
    return settings if settings is not None else get_settings()


def runtime_for_app(request):
    with request.app.state.search_init_lock:
        if getattr(request.app.state, "search_runtime", None) is None:
            request.app.state.search_runtime = RetrievalRuntime(settings_for_app(request))
        return request.app.state.search_runtime


@router.post("/search")
def search_documents(payload: SearchRequest, db: DbSession, user: CurrentUser, request: Request):
    return success(
        request,
        search(db, user, payload, settings_for_app(request), lambda: runtime_for_app(request)),
    )


@router.get("/documents/{document_id}/chunks/{chunk_id}")
def open_chunk(
    document_id: uuid.UUID, chunk_id: uuid.UUID, db: DbSession, user: CurrentUser, request: Request
):
    return success(request, source_chunk(db, user, document_id, chunk_id))


@router.get("/documents/{document_id}/content")
def open_content(document_id: uuid.UUID, db: DbSession, user: CurrentUser, request: Request):
    content, media_type, headers = source_content(db, user, document_id, settings_for_app(request))
    return Response(content, media_type=media_type, headers=headers)
