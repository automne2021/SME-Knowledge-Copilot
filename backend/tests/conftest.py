"""Test chạy trên PostgreSQL thật (cần row locking, partial unique index).

Database test lấy từ TEST_DATABASE_URL, kiểm tra an toàn trước khi tạo/migrate.
Mỗi test chạy trong một transaction và rollback khi kết thúc.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.database_safety import SafeDatabaseTarget, validate_test_database_url
from tests.worker_support import worker_env  # noqa: F401

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy import Engine
    from sqlalchemy.engine import URL
    from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _connection_url(target: SafeDatabaseTarget) -> URL:
    from sqlalchemy.engine import URL

    # Rebuild from validated components, including an explicit port. No libpq
    # query options or second parser may override the target we validated.
    return URL.create(
        "postgresql+psycopg",
        username=target.username,
        password=target.password,
        host=target.host,
        port=target.port,
        database=target.database,
    )


def _ensure_database(url: str | None, development_url: str) -> None:
    target = validate_test_database_url(url, development_url)

    from psycopg import sql
    from sqlalchemy import create_engine, text

    admin_engine = create_engine(
        _connection_url(target).set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 5},
    )
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": target.database},
            ).scalar()
            if not exists:
                statement = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target.database))
                conn.exec_driver_sql(statement.as_string(conn.connection.driver_connection))
    finally:
        admin_engine.dispose()


def _migrate(url: str | None, development_url: str) -> None:
    target = validate_test_database_url(url, development_url)

    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    # configparser coi % là ký tự nội suy.
    cfg.set_main_option(
        "sqlalchemy.url",
        _connection_url(target).render_as_string(hide_password=False).replace("%", "%%"),
    )
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    from app.core.config import get_settings

    settings = get_settings()
    url = settings.test_database_url
    target = validate_test_database_url(url, settings.database_url)
    _ensure_database(url, settings.database_url)
    _migrate(url, settings.database_url)

    from sqlalchemy import create_engine

    engine = create_engine(_connection_url(target), connect_args={"connect_timeout": 5})
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    from sqlalchemy.orm import Session

    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    from fastapi.testclient import TestClient

    from app.core.db import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def people(db_session):
    """Shared identities for auth and upload contracts; rolled back after each test."""
    from app.core.security import hash_password
    from app.models import User, Workspace
    from app.models.enums import UserRole

    first, other = Workspace(name="Workspace A"), Workspace(name="Workspace B")
    db_session.add_all([first, other])
    db_session.flush()
    result = {}
    encoded = hash_password("test-only-password-42")
    for name, role, space in [
        ("member", UserRole.MEMBER, first),
        ("admin", UserRole.KNOWLEDGE_ADMIN, first),
        ("other", UserRole.MEMBER, other),
        ("legacy", UserRole.APPROVER, first),
    ]:
        user = User(
            username="test." + name,
            email=name + "@example.invalid",
            workspace_id=space.id,
            display_name=name,
            role=role,
            password_hash=encoded,
            is_active=True,
        )
        db_session.add(user)
        result[name] = user
    db_session.flush()
    return result
