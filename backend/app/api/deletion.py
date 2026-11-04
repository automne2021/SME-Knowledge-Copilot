"""Admin-only SQL disable, idempotent delete and explicit cleanup retry."""

import uuid

from fastapi import APIRouter, Request, Response

from app.core.db import DbSession
from app.core.errors import success
from app.core.security import AdminUser
from app.services.deletion import delete_document, retry_cleanup

router = APIRouter(tags=["documents"])


@router.delete("/documents/{document_id}")
def remove_document(
    document_id: uuid.UUID, request: Request, response: Response, db: DbSession, user: AdminUser
):
    data, status = delete_document(db, document_id, user)
    response.status_code = status
    return success(request, data)


@router.post("/jobs/{job_id}/retry", status_code=202)
def retry_job(job_id: uuid.UUID, request: Request, db: DbSession, user: AdminUser):
    from app.services.access import job_for_user
    from app.services.retry import retry_document

    job = job_for_user(db, job_id, user)
    if job.kind == "cleanup":
        return success(request, retry_cleanup(db, job_id, user))
    return success(request, retry_document(db, job.document_id, user, expected_job_id=job_id))
