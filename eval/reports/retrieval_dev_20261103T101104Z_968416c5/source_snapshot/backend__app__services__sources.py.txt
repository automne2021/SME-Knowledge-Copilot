"""Authorized active source access; no user-supplied path or rendered document HTML."""

import hashlib
import re
from urllib.parse import quote

from sqlalchemy import select

from app.core.errors import AppError
from app.models import Chunk, Document, DocumentRevision, SourceBlock
from app.services.access import document_for_user, not_found


def active_source(db, document_id, user):
    document = document_for_user(db, document_id, user)
    if document.status != "ready":
        raise AppError(409, "document_not_ready", "Tài liệu chưa sẵn sàng.")
    revision = db.scalar(
        select(DocumentRevision).where(
            DocumentRevision.id == document.active_revision_id,
            DocumentRevision.document_id == document.id,
            DocumentRevision.status == "ready",
        )
    )
    if revision is None or document.active_generation_id is None:
        raise AppError(410, "source_unavailable", "Nguồn không còn khả dụng.")
    return document, revision


def _recheck(db, document, revision_id, generation_id, lifecycle):
    valid = db.scalar(
        select(Document.id).where(
            Document.id == document.id,
            Document.workspace_id == document.workspace_id,
            Document.status == "ready",
            Document.active_revision_id == revision_id,
            Document.active_generation_id == generation_id,
            Document.lifecycle_version == lifecycle,
        )
    )
    if valid is None:
        raise AppError(410, "source_unavailable", "Nguồn đã thay đổi hoặc không còn khả dụng.")


def source_chunk(db, user, document_id, chunk_id):
    document, revision = active_source(db, document_id, user)
    chunk = db.scalar(
        select(Chunk)
        .join(DocumentRevision, Chunk.revision_id == DocumentRevision.id)
        .where(Chunk.id == chunk_id, DocumentRevision.document_id == document.id)
    )
    if chunk is None:
        raise not_found()
    if chunk.revision_id != revision.id or chunk.generation_id != document.active_generation_id:
        raise AppError(410, "source_unavailable", "Bản nguồn trích dẫn không còn khả dụng.")
    _recheck(db, document, revision.id, chunk.generation_id, document.lifecycle_version)
    return {
        "chunk_id": str(chunk.id),
        "document_id": str(document.id),
        "document_version": revision.version,
        "revision_id": str(revision.id),
        "generation_id": str(chunk.generation_id),
        "text": chunk.text,
        "location": chunk.location_json,
        "source_spans": chunk.source_spans_json,
        "file_name": document.filename,
    }


def source_content(db, user, document_id, settings):
    document, revision = active_source(db, document_id, user)
    revision_id, generation_id, lifecycle = (
        revision.id,
        document.active_generation_id,
        document.lifecycle_version,
    )
    filename = re.sub(
        r"[\x00-\x1f\x7f/:]", "_", document.filename.replace("\\", "/").split("/")[-1]
    )[:200]
    if document.mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        blocks = db.scalars(
            select(SourceBlock.raw_text)
            .where(
                SourceBlock.revision_id == revision_id, SourceBlock.generation_id == generation_id
            )
            .order_by(SourceBlock.block_index)
        ).all()
        if not blocks:
            raise AppError(410, "source_unavailable", "Nguồn text không còn khả dụng.")
        content, media_type = "\n".join(blocks).encode("utf-8"), "text/plain"
        filename += ".txt"
    else:
        root = settings.storage_dir.resolve()
        path = (root / revision.storage_key).resolve()
        try:
            if (
                not path.is_relative_to(root)
                or not path.is_file()
                or path.stat().st_size > settings.max_upload_mb * 1024**2
                or path.stat().st_size != document.size_bytes
            ):
                raise OSError
            content = path.read_bytes()
        except OSError as exc:
            raise AppError(410, "source_unavailable", "File nguồn không còn khả dụng.") from exc
        if hashlib.sha256(content).hexdigest() != document.sha256:
            raise AppError(410, "source_unavailable", "File nguồn đã thay đổi.")
        media_type = "application/pdf" if document.mime == "application/pdf" else "text/plain"
    _recheck(db, document, revision_id, generation_id, lifecycle)
    headers = {
        "Content-Disposition": "inline; filename*=UTF-8''" + quote(filename or "source", safe=""),
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
        "Content-Security-Policy": "sandbox; default-src 'none'",
    }
    # Full bounded response; Range is intentionally not advertised or partially served.
    return content, media_type, headers
