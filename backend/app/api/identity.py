from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.core.db import DbSession
from app.core.errors import success
from app.core.security import CurrentUser, bearer, login, logout
from app.schemas.identity import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def public_identity(user) -> dict:
    return {
        "id": user.id,
        "workspace_id": user.workspace_id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
    }


@router.post("/login")
def login_endpoint(payload: LoginRequest, db: DbSession, request: Request) -> dict:
    token, ttl, _ = login(db, payload.username, payload.password.get_secret_value())
    db.commit()
    return success(request, {"access_token": token, "token_type": "bearer", "expires_in": ttl})


@router.get("/me")
def me(user: CurrentUser, request: Request) -> dict:
    return success(request, public_identity(user))


@router.post("/logout")
def logout_endpoint(
    db: DbSession,
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict:
    logout(db, credentials)
    db.commit()
    return success(request, {"revoked": True})
