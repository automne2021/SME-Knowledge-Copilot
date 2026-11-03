"""Upload storage plus compensating cleanup around the SQL transaction."""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass
from email.message import Message
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.models import Document, DocumentRevision, ProcessingJob
from app.services.parsing import PARSER_VERSION

logger = logging.getLogger(__name__)
MIMES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "md": "text/markdown",
}


def file_metadata(
    filename: str | None, content_type: str | None, content_disposition: str = ""
) -> tuple[str, str]:
    header = Message()
    header["Content-Disposition"] = content_disposition
    # python-multipart strips legacy IE/Windows full paths from parsed filenames.
    # Validate the retained raw header too, before trusting its sanitized filename.
    raw_filename = header.get_filename() or filename or ""
    if (
        not filename
        or len(filename) > 255
        or filename.strip() != filename
        or re.search(r"[\\/:\x00-\x1f\x7f]", raw_filename)
        or re.search(r"[\\/:\x00-\x1f\x7f]", filename)
        or filename in {".", ".."}
    ):
        raise AppError(422, "invalid_filename", "Tên file không hợp lệ.")
    extension = Path(filename).suffix.lower().lstrip(".")
    accepted = {MIMES.get(extension), "application/octet-stream"}
    if extension == "md":
        accepted.add("text/plain")
    if extension not in MIMES or (content_type or "").split(";")[0].lower() not in accepted:
        raise AppError(415, "unsupported_file_type", "Chỉ hỗ trợ PDF, DOCX, TXT và MD.")
    return filename, extension


def validate_signature(path: Path, extension: str) -> None:
    with path.open("rb") as stream:
        prefix = stream.read(1024)
    valid = (
        prefix.startswith(b"%PDF-")
        if extension == "pdf"
        else prefix.startswith(b"PK\x03\x04")
        if extension == "docx"
        else not prefix.startswith((b"%PDF-", b"PK\x03\x04")) and b"\x00" not in prefix
    )
    if not valid:
        raise AppError(415, "unsupported_file_type", "Nội dung không khớp định dạng file.")


@dataclass
class StoredUpload:
    path: Path
    storage_key: str
    sha256: str
    size_bytes: int
    document_id: uuid.UUID
    revision_id: uuid.UUID


async def store_stream(
    file, root: Path, workspace_id: uuid.UUID, extension: str, maximum: int
) -> StoredUpload:
    document_id, revision_id = uuid.uuid4(), uuid.uuid4()
    # Flat UUID keys also avoid Windows MAX_PATH with nested test/deployment roots.
    key = f"{workspace_id.hex}/{revision_id.hex}.{extension}"
    root = root.resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root):
        raise AppError(500, "storage_error", "Không thể lưu tài liệu.")
    digest = hashlib.sha256()
    size = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as output:
            while data := await file.read(64 * 1024):
                size += len(data)
                if size > maximum:
                    raise AppError(413, "file_too_large", "File vượt giới hạn dung lượng.")
                digest.update(data)
                output.write(data)
        validate_signature(path, extension)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return StoredUpload(path, key, digest.hexdigest(), size, document_id, revision_id)


def register_upload(db, user, filename: str, extension: str, stored: StoredUpload) -> dict:
    document = Document(
        id=stored.document_id,
        workspace_id=user.workspace_id,
        created_by=user.id,
        filename=filename,
        mime=MIMES[extension],
        size_bytes=stored.size_bytes,
        sha256=stored.sha256,
    )
    revision = DocumentRevision(
        id=stored.revision_id,
        document_id=stored.document_id,
        storage_key=stored.storage_key,
        parser_version=PARSER_VERSION,
    )
    job = ProcessingJob(
        id=uuid.uuid4(),
        entity_type="document",
        entity_id=stored.document_id,
        document_id=stored.document_id,
        revision_id=stored.revision_id,
        kind="ingest",
        stage="validate",
    )
    try:
        with db.begin_nested():
            db.add(document)
            db.flush()
            db.add(revision)
            db.flush()
            db.add(job)
            db.flush()
    except IntegrityError as exc:
        stored.path.unlink(missing_ok=True)
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if constraint == "uq_documents_workspace_hash_live":
            existing = db.scalar(
                select(Document).where(
                    Document.workspace_id == user.workspace_id,
                    Document.sha256 == stored.sha256,
                    Document.status != "deleted",
                )
            )
            if existing:
                raise AppError(
                    409,
                    "duplicate_document",
                    "Tài liệu đã tồn tại.",
                    {"document_id": str(existing.id), "status": existing.status},
                ) from None
        raise
    except BaseException:
        stored.path.unlink(missing_ok=True)
        raise
    try:
        db.commit()
    except Exception:
        # Commit acknowledgement can be lost after PostgreSQL committed. Never delete a
        # potentially committed source merely because the client saw a connection error.
        try:
            db.rollback()
            exists = db.scalar(
                select(DocumentRevision.id).where(DocumentRevision.id == stored.revision_id)
            )
            if not exists:
                stored.path.unlink(missing_ok=True)
        except Exception:
            logger.error("upload_commit_uncertain document_id=%s", stored.document_id)
        raise
    return {"document_id": document.id, "job_id": job.id, "status": document.status}
