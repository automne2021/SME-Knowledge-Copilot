"""Migration on a populated legacy schema, isolated in a rolled-back test-DB transaction."""

import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture
def migration_db(db_engine):
    with db_engine.connect() as connection:
        transaction = connection.begin()
        schema = "migration_test_" + uuid.uuid4().hex
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
        cfg = Config(str(BACKEND / "alembic.ini"))
        cfg.set_main_option("script_location", str(BACKEND / "alembic"))
        cfg.set_main_option(
            "sqlalchemy.url", db_engine.url.render_as_string(hide_password=False).replace("%", "%%")
        )
        cfg.attributes["connection"] = connection
        try:
            yield connection, cfg
        finally:
            transaction.rollback()


def test_upgrade_preserves_legacy_rows_and_safe_identity_backfill(migration_db):
    c, cfg = migration_db
    command.upgrade(cfg, "27b126c3c0bc")
    workspace, user, job = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    c.execute(
        text("INSERT INTO workspaces(id,name) VALUES(:id,'Legacy workspace')"), {"id": workspace}
    )
    c.execute(
        text(
            "INSERT INTO users(id,workspace_id,email,display_name,password_hash,role) "
            "VALUES(:id,:w,'legacy@example.invalid','Legacy','preserve-hash','approver')"
        ),
        {"id": user, "w": workspace},
    )
    c.execute(
        text(
            "INSERT INTO processing_jobs(id,entity_type,entity_id,status,attempts) "
            "VALUES(:id,'meeting',:entity,'processing',1)"
        ),
        {"id": job, "entity": uuid.uuid4()},
    )
    command.upgrade(cfg, "head")
    row = c.execute(
        text("SELECT username,is_active,role,password_hash,email FROM users WHERE id=:id"),
        {"id": user},
    ).one()
    assert row == (
        "legacy_" + user.hex,
        False,
        "approver",
        "preserve-hash",
        "legacy@example.invalid",
    )
    assert c.execute(
        text("SELECT status,kind,document_id FROM processing_jobs WHERE id=:id"), {"id": job}
    ).one() == ("processing", None, None)
    # Roundtrip is allowed only while no RAG data has been created.
    command.downgrade(cfg, "27b126c3c0bc")
    assert c.execute(
        text("SELECT role,password_hash FROM users WHERE id=:id"), {"id": user}
    ).one() == ("approver", "preserve-hash")
    command.upgrade(cfg, "head")
    assert c.execute(text("SELECT count(*) FROM users")).scalar() == 1


def test_downgrade_refuses_to_destroy_new_domain_data(migration_db):
    c, cfg = migration_db
    command.upgrade(cfg, "head")
    workspace = uuid.uuid4()
    c.execute(text("INSERT INTO workspaces(id,name) VALUES(:id,'Demo')"), {"id": workspace})
    c.execute(
        text(
            "INSERT INTO eval_runs(id,workspace_id,dataset_version,corpus_version,"
            "git_commit,config_json,results_path) "
            "VALUES(:id,:w,'v1','v1','commit','{}','report')"
        ),
        {"id": uuid.uuid4(), "w": workspace},
    )
    with pytest.raises(RuntimeError, match="Refusing downgrade with RAG data"):
        command.downgrade(cfg, "27b126c3c0bc")
    assert c.execute(text("SELECT count(*) FROM eval_runs")).scalar() == 1
