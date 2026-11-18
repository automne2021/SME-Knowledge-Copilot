"""Workspace-scoped folder CRUD. SQL constraints also protect non-API writers."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Document, Folder, User
from app.services.access import not_found


def folder_data(folder: Folder, ready_document_count: int = 0) -> dict:
    return {
        "id": folder.id,
        "name": folder.name,
        "created_at": folder.created_at,
        "updated_at": folder.updated_at,
        "ready_document_count": ready_document_count,
    }


def ready_count(db: Session, folder: Folder) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Document)
        .where(
            Document.workspace_id == folder.workspace_id,
            Document.folder_id == folder.id,
            Document.status == "ready",
        )
    )


def list_folders(db: Session, user: User) -> list[dict]:
    # The status predicate belongs in the join so empty folders remain in the result.
    rows = db.execute(
        select(Folder, func.count(Document.id))
        .outerjoin(
            Document,
            (Document.folder_id == Folder.id)
            & (Document.workspace_id == Folder.workspace_id)
            & (Document.status == "ready"),
        )
        .where(Folder.workspace_id == user.workspace_id)
        .group_by(Folder.id)
        .order_by(func.lower(Folder.name), Folder.id)
    ).all()
    return [folder_data(folder, count) for folder, count in rows]


def locked_folder(db: Session, folder_id: uuid.UUID, user: User) -> Folder:
    folder = db.scalar(
        select(Folder)
        .where(Folder.id == folder_id, Folder.workspace_id == user.workspace_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if folder is None:
        raise not_found()
    return folder


def save_folder(db: Session, folder: Folder) -> Folder:
    try:
        db.add(folder)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig.diag, "constraint_name", None) == "uq_folders_workspace_name_ci":
            raise AppError(409, "duplicate_folder", "Tên thư mục đã tồn tại") from None
        raise
    return folder


def create_folder(db: Session, user: User, name: str) -> Folder:
    return save_folder(db, Folder(workspace_id=user.workspace_id, created_by=user.id, name=name))


def rename_folder(db: Session, folder_id: uuid.UUID, user: User, name: str) -> Folder:
    folder = locked_folder(db, folder_id, user)
    folder.name = name
    return save_folder(db, folder)


def delete_folder(db: Session, folder_id: uuid.UUID, user: User) -> None:
    folder = locked_folder(db, folder_id, user)
    # FOR UPDATE conflicts with the FK key-share lock taken by a concurrent attachment.
    # Any attached row (including a tombstone) makes the folder nonempty.
    if db.scalar(select(Document.id).where(Document.folder_id == folder.id).limit(1)):
        raise AppError(409, "folder_not_empty", "Thư mục vẫn còn tài liệu")
    db.delete(folder)
    db.commit()
