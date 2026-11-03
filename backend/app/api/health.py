from fastapi import APIRouter, Request
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.db import DbSession
from app.core.errors import AppError, success

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: DbSession, request: Request) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise AppError(503, "database_unavailable", "Không kết nối được database") from exc
    return success(request, {"status": "ok", "database": "ok"})
