"""Resource resolution is scoped before status checks; IDs are never authorization."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import ChatSession, Document, ProcessingJob, QueryRun, User
from app.models.enums import DocumentStatus


def not_found() -> AppError:
    return AppError(404, "not_found", "Không tìm thấy tài nguyên")


def document_for_user(db: Session, document_id: uuid.UUID, user: User) -> Document:
    document = db.scalar(
        select(Document).where(
            Document.id == document_id, Document.workspace_id == user.workspace_id
        )
    )
    if document is None:
        raise not_found()
    if document.status in {DocumentStatus.DELETING, DocumentStatus.DELETED}:
        raise AppError(410, "source_unavailable", "Nguồn tài liệu không còn khả dụng")
    return document


def session_for_user(db: Session, session_id: uuid.UUID, user: User) -> ChatSession:
    session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.workspace_id == user.workspace_id,
            ChatSession.created_by == user.id,
        )
    )
    if session is None:
        raise not_found()
    return session


def run_for_user(db: Session, run_id: uuid.UUID, user: User) -> QueryRun:
    run = db.scalar(
        select(QueryRun)
        .join(ChatSession, QueryRun.session_id == ChatSession.id)
        .where(
            QueryRun.id == run_id,
            ChatSession.workspace_id == user.workspace_id,
            ChatSession.created_by == user.id,
        )
    )
    if run is None:
        raise not_found()
    return run


def job_for_user(db: Session, job_id: uuid.UUID, user: User) -> ProcessingJob:
    job = db.scalar(
        select(ProcessingJob)
        .join(Document, ProcessingJob.document_id == Document.id)
        .where(
            ProcessingJob.id == job_id,
            Document.workspace_id == user.workspace_id,
        )
    )
    if job is None:
        raise not_found()
    return job
