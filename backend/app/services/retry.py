"""Authorized, idempotent manual retry of transient ingestion failures."""

import uuid

from sqlalchemy import select

from app.core.errors import AppError
from app.models import Document, DocumentRevision, ProcessingJob


def retry_document(db, document_id, user, expected_job_id=None):
    document = db.scalar(
        select(Document)
        .where(Document.id == document_id, Document.workspace_id == user.workspace_id)
        .with_for_update()
    )
    if document is None:
        raise AppError(404, "not_found", "Không tìm thấy tài liệu.")
    if document.status in {"deleting", "deleted"}:
        raise AppError(410, "source_unavailable", "Nguồn không còn khả dụng.")
    active = db.scalar(
        select(ProcessingJob).where(
            ProcessingJob.document_id == document.id,
            ProcessingJob.kind == "ingest",
            ProcessingJob.status.in_(["queued", "running", "retry_wait"]),
        )
    )
    if active:
        return {"document_id": document.id, "job_id": active.id, "status": document.status}
    latest = db.scalar(
        select(ProcessingJob)
        .where(ProcessingJob.document_id == document.id, ProcessingJob.kind == "ingest")
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
        .limit(1)
    )
    if (
        document.status != "failed"
        or latest is None
        or latest.status != "failed"
        or not latest.retryable
        or latest.revision_id is None
        or (expected_job_id is not None and latest.id != expected_job_id)
    ):
        raise AppError(409, "retry_not_allowed", "Tài liệu không thể retry với lỗi hiện tại.")
    revision = db.get(DocumentRevision, latest.revision_id)
    document.status, revision.status = "queued", "staging"
    job = ProcessingJob(
        id=uuid.uuid4(),
        entity_type="document",
        entity_id=document.id,
        document_id=document.id,
        revision_id=revision.id,
        kind="ingest",
        stage="validate",
    )
    db.add(job)
    db.flush()
    db.commit()
    return {"document_id": document.id, "job_id": job.id, "status": document.status}
