"""Workspace-scoped document classification without reindexing or lifecycle changes."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Document, Folder, User
from app.services.access import not_found


def folder_for_user(db: Session, folder_id: uuid.UUID, user: User, *, lock: bool = False) -> Folder:
    statement = select(Folder).where(
        Folder.id == folder_id, Folder.workspace_id == user.workspace_id
    )
    if lock:
        # FOR KEY SHARE prevents folder deletion through attachment commit, while
        # allowing other attachments. Folder locks precede document locks.
        statement = statement.with_for_update(read=True, key_share=True)
    folder = db.scalar(statement)
    if folder is None:
        raise not_found()
    return folder


def move_document(
    db: Session, document_id: uuid.UUID, user: User, folder_id: uuid.UUID | None
) -> Document:
    if folder_id is not None:
        folder_for_user(db, folder_id, user, lock=True)
    document = db.scalar(
        select(Document)
        .where(Document.id == document_id, Document.workspace_id == user.workspace_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if document is None:
        raise not_found()
    if document.status in {"deleting", "deleted"}:
        raise AppError(410, "source_unavailable", "Nguồn tài liệu không còn khả dụng")
    document.folder_id = folder_id
    db.commit()
    return document
