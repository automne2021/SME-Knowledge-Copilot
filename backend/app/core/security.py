"""Demo bearer identity: Argon2id passwords; only SHA-256 of random tokens is persisted."""

import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Annotated

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import DbSession
from app.core.errors import AppError
from app.models import AuthToken, User
from app.models.enums import UserRole

HASHER = PasswordHasher(
    time_cost=2, memory_cost=19456, parallelism=1, hash_len=32, salt_len=16, type=Type.ID
)
RAG_ROLES = {UserRole.MEMBER, UserRole.KNOWLEDGE_ADMIN}
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    if not 12 <= len(password) <= 128:
        raise ValueError("Seed password must contain 12 to 128 characters")
    return HASHER.hash(password)


def verify_password(encoded: str, password: str) -> bool:
    try:
        return HASHER.verify(encoded, password)
    except (VerificationError, ValueError):
        return False


@lru_cache(maxsize=1)
def dummy_hash() -> str:
    return HASHER.hash(secrets.token_urlsafe(32))


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def unauthorized() -> AppError:
    return AppError(401, "unauthorized", "Thông tin đăng nhập hoặc phiên truy cập không hợp lệ")


def login(db: Session, username: str, password: str) -> tuple[str, int, User]:
    user = db.scalar(select(User).where(User.username == username))
    valid = verify_password(user.password_hash if user else dummy_hash(), password)
    if not valid or user is None or not user.is_active or user.role not in RAG_ROLES:
        raise unauthorized()
    token = secrets.token_urlsafe(32)
    ttl = get_settings().auth_token_ttl_seconds
    db.add(
        AuthToken(
            user_id=user.id,
            token_hash=token_digest(token),
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl),
        )
    )
    db.flush()
    return token, ttl, user


def active_token(db: Session, credentials: HTTPAuthorizationCredentials | None) -> AuthToken:
    if credentials is None or not re.fullmatch(r"[A-Za-z0-9_-]{43}", credentials.credentials):
        raise unauthorized()
    token = db.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == token_digest(credentials.credentials),
            AuthToken.expires_at > func.now(),
            AuthToken.revoked_at.is_(None),
        )
    )
    if token is None:
        raise unauthorized()
    return token


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    token = active_token(db, credentials)
    user = db.get(User, token.user_id)
    if user is None or not user.is_active or user.role not in RAG_ROLES:
        raise unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def logout(db: Session, credentials: HTTPAuthorizationCredentials | None) -> None:
    """Revoke only the presented token; other sessions of the same user stay valid."""
    token = active_token(db, credentials)
    token.revoked_at = datetime.now(UTC)
    db.flush()


def require_admin(user: User) -> User:
    if user.role != UserRole.KNOWLEDGE_ADMIN:
        raise AppError(403, "forbidden", "Bạn không có quyền thực hiện thao tác này")
    return user


def get_admin(user: CurrentUser) -> User:
    return require_admin(user)


AdminUser = Annotated[User, Depends(get_admin)]
