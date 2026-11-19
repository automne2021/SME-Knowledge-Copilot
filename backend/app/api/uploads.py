"""Admin document writes: bounded multipart upload and scoped manual retry."""

import uuid

from fastapi import APIRouter, Request
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartException

from app.core.config import get_settings
from app.core.db import DbSession
from app.core.errors import AppError, success
from app.core.security import AdminUser
from app.services.retry import retry_document
from app.services.uploads import file_metadata, register_upload, store_stream

router = APIRouter(tags=["documents"])


@router.post("/documents/{document_id}/retry", status_code=202)
def retry_ingestion(document_id: uuid.UUID, request: Request, db: DbSession, user: AdminUser):
    return success(request, retry_document(db, document_id, user))


@router.post(
    "/documents",
    status_code=202,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "additionalProperties": False,
                        "properties": {
                            "file": {"type": "string", "format": "binary"},
                            "folder_id": {"type": "string", "format": "uuid"},
                        },
                    }
                }
            },
        }
    },
)
async def upload_document(request: Request, db: DbSession, user: AdminUser) -> dict:
    settings = get_settings()
    maximum = settings.max_upload_mb * 1024**2
    request_limit = maximum + 64 * 1024  # bounded multipart framing overhead
    length = request.headers.get("content-length")
    if length is not None:
        try:
            size = int(length)
            if size < 0:
                raise ValueError
        except ValueError:
            raise AppError(400, "invalid_request", "Content-Length không hợp lệ.") from None
        if size > request_limit:
            raise AppError(413, "file_too_large", "Request vượt giới hạn dung lượng.")
    received = 0
    exceeded = False

    async def receive():
        nonlocal received, exceeded
        message = await request.receive()
        received += len(message.get("body", b""))
        if received > request_limit:
            exceeded = True
            # MultipartParser closes any already-spooled files on this exception.
            raise MultiPartException("Request body limit exceeded")
        return message

    bounded_request = Request(request.scope, receive=receive)
    try:
        async with bounded_request.form(max_files=1, max_fields=1) as form:
            items = list(form.multi_items())
            keys = [key for key, _ in items]
            if (
                keys.count("file") != 1
                or keys.count("folder_id") > 1
                or set(keys) - {"file", "folder_id"}
                or not isinstance(form["file"], UploadFile)
            ):
                raise AppError(422, "invalid_upload", "Chỉ chấp nhận file và folder_id tùy chọn.")
            folder_id = None
            if "folder_id" in form:
                try:
                    folder_id = uuid.UUID(form["folder_id"])
                except (ValueError, TypeError, AttributeError):
                    raise AppError(422, "invalid_upload", "folder_id phải là UUID.") from None
            file = form["file"]
            filename, extension = file_metadata(
                file.filename, file.content_type, file.headers.get("content-disposition", "")
            )
            stored = await store_stream(
                file, settings.storage_dir, user.workspace_id, extension, maximum
            )
            return success(
                request, register_upload(db, user, filename, extension, stored, folder_id)
            )
    except HTTPException:
        if exceeded:
            raise AppError(413, "file_too_large", "Request vượt giới hạn dung lượng.") from None
        raise AppError(422, "invalid_upload", "Multipart upload không hợp lệ.") from None
