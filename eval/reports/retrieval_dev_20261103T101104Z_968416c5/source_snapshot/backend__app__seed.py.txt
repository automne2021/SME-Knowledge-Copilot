"""Idempotent seed for one demo workspace. Secrets only come from the private environment."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_sessionmaker
from app.core.security import hash_password
from app.models import User, Workspace
from app.models.enums import UserRole

WORKSPACE_ID = uuid.uuid5(uuid.NAMESPACE_URL, "sme-knowledge-copilot/demo")


def seed_demo(db: Session, settings: Settings) -> dict:
    definitions = [
        ("demo.admin", "Knowledge Admin", UserRole.KNOWLEDGE_ADMIN, settings.demo_admin_password),
        ("demo.member", "Demo Member", UserRole.MEMBER, settings.demo_member_password),
    ]
    # Validate every password before doing any writes; never log or return its value.
    if any(
        secret is None or not 12 <= len(secret.get_secret_value()) <= 128
        for _, _, _, secret in definitions
    ):
        raise ValueError(
            "Configure both DEMO_ADMIN_PASSWORD and DEMO_MEMBER_PASSWORD (12–128 chars)"
        )
    if definitions[0][3].get_secret_value() == definitions[1][3].get_secret_value():
        raise ValueError("Use different demo admin/member passwords")
    workspace = db.get(Workspace, WORKSPACE_ID)
    if workspace is None:
        workspace = Workspace(id=WORKSPACE_ID, name="SME Knowledge Demo")
        db.add(workspace)
        db.flush()
    created = 0
    for username, display_name, role, secret in definitions:
        expected_id = uuid.uuid5(WORKSPACE_ID, username)
        user = db.scalar(select(User).where(User.username == username))
        if user is not None:
            if (
                user.id != expected_id
                or user.workspace_id != workspace.id
                or user.role != role
                or not user.is_active
            ):
                raise ValueError("Seed identity conflict; review existing data explicitly")
            continue  # Do not silently reset credentials or grant privileges on repeat seed.
        if db.get(User, expected_id) is not None:
            raise ValueError("Seed ID conflict; review existing data explicitly")
        db.add(
            User(
                id=expected_id,
                workspace_id=workspace.id,
                username=username,
                email=username + "@demo.invalid",
                display_name=display_name,
                role=role,
                password_hash=hash_password(secret.get_secret_value()),
                is_active=True,
            )
        )
        created += 1
    db.flush()
    return {
        "workspace_id": str(workspace.id),
        "users_created": created,
        "usernames": [row[0] for row in definitions],
    }


if __name__ == "__main__":
    import json

    try:
        with get_sessionmaker()() as db, db.begin():
            result = seed_demo(db, get_settings())
    except (SQLAlchemyError, ValueError) as exc:
        raise SystemExit(
            f"Seed failed ({type(exc).__name__}); review config/data; no commit."
        ) from None
    print(json.dumps(result))
