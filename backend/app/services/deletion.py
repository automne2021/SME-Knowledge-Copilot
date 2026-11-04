"""Disable in SQL first. Cleanup is durable and never re-enables a document."""

import uuid

from sqlalchemy import func, select

from app.core.errors import AppError
from app.models import Document, ProcessingJob
from app.services.privacy import redact_document

ACTIVE = ("queued", "running", "retry_wait")


def locked_document(db, document_id, user):
    row = db.scalar(
        select(Document)
        .where(Document.id == document_id, Document.workspace_id == user.workspace_id)
        .with_for_update()
    )
    if row is None:
        raise AppError(404, "not_found", "Không tìm thấy tài liệu.")
    return row


def delete_document(db, document_id, user):
    document = locked_document(db, document_id, user)
    latest = db.scalar(
        select(ProcessingJob)
        .where(ProcessingJob.document_id == document.id, ProcessingJob.kind == "cleanup")
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
        .limit(1)
    )
    if document.status in {"deleting", "deleted"}:
        db.commit()
        return {
            "document_id": document.id,
            "status": document.status,
            "job_id": latest.id if latest else None,
        }, 200 if document.status == "deleted" else 202
    now = db.scalar(select(func.clock_timestamp()))
    document.status, document.deleted_at = "deleting", now
    document.lifecycle_version += 1
    document.active_revision_id = document.active_generation_id = None
    jobs = db.scalars(
        select(ProcessingJob)
        .where(
            ProcessingJob.document_id == document.id,
            ProcessingJob.kind == "ingest",
            ProcessingJob.status.in_(ACTIVE),
        )
        .order_by(ProcessingJob.id)
        .with_for_update()
    ).all()
    for job in jobs:
        job.status, job.finished_at, job.next_retry_at = "cancelled", now, None
        job.lease_token = job.lease_expires_at = None
        job.error_message, job.retryable = None, False
    redact_document(db, document)
    job = ProcessingJob(
        id=uuid.uuid4(),
        entity_type="document",
        entity_id=document.id,
        document_id=document.id,
        kind="cleanup",
        stage="cleanup",
    )
    db.add(job)
    db.flush()
    db.commit()
    return {"document_id": document.id, "job_id": job.id, "status": document.status}, 202


def retry_cleanup(db, job_id, user):
    # Resolve scope before lock/status; lock order remains document -> job.
    document_id = db.scalar(
        select(ProcessingJob.document_id)
        .join(Document, Document.id == ProcessingJob.document_id)
        .where(ProcessingJob.id == job_id, Document.workspace_id == user.workspace_id)
    )
    if document_id is None:
        raise AppError(404, "not_found", "Không tìm thấy job.")
    document = locked_document(db, document_id, user)
    job = db.scalar(select(ProcessingJob).where(ProcessingJob.id == job_id).with_for_update())
    if job.kind != "cleanup" or document.status != "deleting":
        raise AppError(409, "retry_not_allowed", "Job không thể retry cleanup.")
    active = db.scalar(
        select(ProcessingJob).where(
            ProcessingJob.document_id == document.id,
            ProcessingJob.kind == "cleanup",
            ProcessingJob.status.in_(ACTIVE),
        )
    )
    if active:
        db.commit()
        return {"document_id": document.id, "job_id": active.id, "status": document.status}
    latest = db.scalar(
        select(ProcessingJob.id)
        .where(ProcessingJob.document_id == document.id, ProcessingJob.kind == "cleanup")
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
        .limit(1)
    )
    if latest != job.id or job.status != "failed" or not job.retryable:
        raise AppError(409, "retry_not_allowed", "Cleanup không có lỗi tạm thời để retry.")
    new_job = ProcessingJob(
        id=uuid.uuid4(),
        entity_type="document",
        entity_id=document.id,
        document_id=document.id,
        kind="cleanup",
        stage="cleanup",
    )
    db.add(new_job)
    db.flush()
    db.commit()
    return {"document_id": document.id, "job_id": new_job.id, "status": document.status}
