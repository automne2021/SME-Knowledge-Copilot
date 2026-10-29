from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.db import DbSession
from app.core.errors import AppError

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: DbSession) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise AppError(503, "database_unavailable", "Không kết nối được database") from exc
    return {"status": "ok", "database": "ok"}
