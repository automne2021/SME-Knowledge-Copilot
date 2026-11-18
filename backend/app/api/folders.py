"""All workspace members can list folders; only knowledge admins can change them."""

import uuid

from fastapi import APIRouter, Request

from app.core.db import DbSession
from app.core.errors import success
from app.core.security import AdminUser, CurrentUser
from app.schemas.folders import FolderName
from app.services.folders import (
    create_folder,
    delete_folder,
    folder_data,
    list_folders,
    ready_count,
    rename_folder,
)

router = APIRouter(tags=["folders"])


@router.get("/folders")
def folders(db: DbSession, user: CurrentUser, request: Request) -> dict:
    return success(request, {"items": list_folders(db, user)})


@router.post("/folders", status_code=201)
def create(payload: FolderName, db: DbSession, user: AdminUser, request: Request) -> dict:
    return success(request, folder_data(create_folder(db, user, payload.name)))


@router.patch("/folders/{folder_id}")
def rename(
    folder_id: uuid.UUID, payload: FolderName, db: DbSession, user: AdminUser, request: Request
) -> dict:
    folder = rename_folder(db, folder_id, user, payload.name)
    return success(request, folder_data(folder, ready_count(db, folder)))


@router.delete("/folders/{folder_id}")
def delete(folder_id: uuid.UUID, db: DbSession, user: AdminUser, request: Request) -> dict:
    delete_folder(db, folder_id, user)
    return success(request, {"id": folder_id, "deleted": True})
