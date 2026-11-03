"""Scoped resource metadata/history. Search, cleanup and answering remain later steps."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Request
from sqlalchemy import case, func, select

from app.core.db import DbSession
from app.core.errors import success
from app.core.security import CurrentUser
from app.models import (
    AnswerCitation,
    ChatMessage,
    ChatSession,
    Chunk,
    Document,
    DocumentRevision,
    ProcessingJob,
)
from app.schemas.identity import SessionCreate
from app.services.access import document_for_user, job_for_user, run_for_user, session_for_user

router = APIRouter(tags=["resources"])
PageLimit = Annotated[int, Query(ge=1, le=100)]


def document_data(document: Document, latest_job_id=None) -> dict:
    return {
        key: getattr(document, key)
        for key in (
            "id",
            "filename",
            "mime",
            "size_bytes",
            "status",
            "active_revision_id",
            "created_at",
        )
    } | {"warnings": document.warnings_json, "latest_job_id": latest_job_id}


def latest_jobs(db, ids):
    ranked = (
        select(
            ProcessingJob.document_id,
            ProcessingJob.id,
            func.row_number()
            .over(
                partition_by=ProcessingJob.document_id,
                order_by=[
                    case(
                        (ProcessingJob.status.in_(["queued", "running", "retry_wait"]), 0), else_=1
                    ),
                    ProcessingJob.created_at.desc(),
                    ProcessingJob.id.desc(),
                ],
            )
            .label("position"),
        )
        .where(ProcessingJob.document_id.in_(ids))
        .subquery()
    )
    jobs = db.execute(select(ranked.c.document_id, ranked.c.id).where(ranked.c.position == 1)).all()
    return dict(jobs)


@router.get("/documents")
def documents(db: DbSession, user: CurrentUser, request: Request, limit: PageLimit = 50) -> dict:
    rows = db.scalars(
        select(Document)
        .where(Document.workspace_id == user.workspace_id, Document.status != "deleted")
        .order_by(Document.created_at.desc(), Document.id)
        .limit(limit)
    ).all()
    jobs = latest_jobs(db, [row.id for row in rows])
    return success(request, {"items": [document_data(row, jobs.get(row.id)) for row in rows]})


@router.get("/documents/{document_id}")
def document(document_id: uuid.UUID, db: DbSession, user: CurrentUser, request: Request) -> dict:
    row = document_for_user(db, document_id, user)
    return success(request, document_data(row, latest_jobs(db, [row.id]).get(row.id)))


@router.get("/jobs/{job_id}")
def job(job_id: uuid.UUID, db: DbSession, user: CurrentUser, request: Request) -> dict:
    row = job_for_user(db, job_id, user)
    return success(
        request,
        {
            key: getattr(row, key)
            for key in (
                "id",
                "document_id",
                "kind",
                "status",
                "stage",
                "attempts",
                "retryable",
                "error_code",
            )
        }
        | {
            "progress": row.attempt_manifest_json.get("progress"),
            "timings_ms": row.attempt_manifest_json.get("timings_ms"),
        },
    )


@router.post("/chat/sessions", status_code=201)
def create_session(
    payload: SessionCreate, db: DbSession, user: CurrentUser, request: Request
) -> dict:
    row = ChatSession(workspace_id=user.workspace_id, created_by=user.id, title=payload.title)
    db.add(row)
    db.flush()
    db.commit()
    return success(request, {"id": row.id, "title": row.title, "created_at": row.created_at})


@router.get("/chat/sessions")
def sessions(db: DbSession, user: CurrentUser, request: Request, limit: PageLimit = 50) -> dict:
    rows = db.scalars(
        select(ChatSession)
        .where(ChatSession.workspace_id == user.workspace_id, ChatSession.created_by == user.id)
        .order_by(ChatSession.created_at.desc(), ChatSession.id)
        .limit(limit)
    ).all()
    return success(
        request,
        {
            "items": [
                {"id": row.id, "title": row.title, "created_at": row.created_at} for row in rows
            ]
        },
    )


@router.get("/chat/sessions/{session_id}/messages")
def messages(
    session_id: uuid.UUID, db: DbSession, user: CurrentUser, request: Request, limit: PageLimit = 50
) -> dict:
    session_for_user(db, session_id, user)
    rows = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
        .limit(limit)
    ).all()
    # Check current SQL source state as well as the stored redaction flag. Cleanup
    # may lag behind the soft delete; admin is still restricted to their own session.
    hidden = set()
    if rows:
        source_rows = db.execute(
            select(
                AnswerCitation.message_id,
                Document.status,
                Document.workspace_id,
                Chunk.id,
                Document.active_revision_id,
                Document.active_generation_id,
                AnswerCitation.revision_id,
                AnswerCitation.generation_id,
                DocumentRevision.status,
                AnswerCitation.source_status,
            )
            .join(Document, AnswerCitation.document_id == Document.id)
            .join(DocumentRevision, AnswerCitation.revision_id == DocumentRevision.id)
            .outerjoin(
                Chunk,
                (AnswerCitation.chunk_id == Chunk.id)
                & (AnswerCitation.revision_id == Chunk.revision_id)
                & (AnswerCitation.generation_id == Chunk.generation_id),
            )
            .where(AnswerCitation.message_id.in_([row.id for row in rows]))
        ).all()
        cited = {row[0] for row in source_rows}
        for row in rows:
            if (
                row.role == "assistant"
                and row.answer_status != "insufficient_evidence"
                and row.id not in cited
            ):
                hidden.add(row.id)
        for (
            message_id,
            status,
            workspace_id,
            chunk_id,
            active_rev,
            active_gen,
            rev,
            gen,
            revision_status,
            citation_status,
        ) in source_rows:
            if (
                status != "ready"
                or workspace_id != user.workspace_id
                or chunk_id is None
                or active_rev != rev
                or active_gen != gen
                or revision_status != "ready"
                or citation_status != "available"
            ):
                hidden.add(message_id)
    # No citation snapshots/config traces are exposed by this foundation endpoint.
    return success(
        request,
        {
            "items": [
                {
                    "id": row.id,
                    "role": row.role,
                    "content": "" if row.source_unavailable or row.id in hidden else row.content,
                    "source_unavailable": row.source_unavailable or row.id in hidden,
                    "created_at": row.created_at,
                }
                for row in rows
            ]
        },
    )


@router.get("/chat/runs/{run_id}")
def query_run(run_id: uuid.UUID, db: DbSession, user: CurrentUser, request: Request) -> dict:
    row = run_for_user(db, run_id, user)
    return success(
        request,
        {
            "id": row.id,
            "session_id": row.session_id,
            "status": row.status,
            "error_code": row.error_code,
        },
    )
