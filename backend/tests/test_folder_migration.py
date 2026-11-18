"""Upgrade existing RAG data, downgrade guard and metadata drift on real PostgreSQL."""

import uuid

import pytest
from alembic import command
from sqlalchemy import text

from tests import test_rag_migration

migration_db = test_rag_migration.migration_db


def test_folder_upgrade_preserves_existing_documents_and_roundtrips(migration_db):
    connection, config = migration_db
    command.upgrade(config, "20261103_rag04")
    workspace, user, document = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    connection.execute(
        text("INSERT INTO workspaces(id,name) VALUES(:id,'Existing')"), {"id": workspace}
    )
    connection.execute(
        text(
            "INSERT INTO users(id,workspace_id,username,email,display_name,password_hash,role) "
            "VALUES(:id,:w,'existing.user','existing@example.invalid','Existing','unused','member')"
        ),
        {"id": user, "w": workspace},
    )
    connection.execute(
        text(
            "INSERT INTO documents(id,workspace_id,created_by,filename,mime,"
            "size_bytes,sha256,status) "
            "VALUES(:id,:w,:u,'existing.txt','text/plain',10,:hash,'queued')"
        ),
        {"id": document, "w": workspace, "u": user, "hash": "a" * 64},
    )
    command.upgrade(config, "head")
    assert connection.execute(
        text("SELECT folder_id,workspace_id,filename FROM documents WHERE id=:id"), {"id": document}
    ).one() == (None, workspace, "existing.txt")
    command.check(config)
    command.downgrade(config, "20261103_rag04")
    assert connection.execute(text("SELECT count(*) FROM documents")).scalar() == 1
    command.upgrade(config, "head")
    command.check(config)


def test_folder_downgrade_refuses_data_loss(migration_db):
    connection, config = migration_db
    command.upgrade(config, "head")
    workspace, user, folder = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    connection.execute(
        text("INSERT INTO workspaces(id,name) VALUES(:id,'Folder test')"), {"id": workspace}
    )
    connection.execute(
        text(
            "INSERT INTO users(id,workspace_id,username,email,display_name,password_hash,role) "
            "VALUES(:id,:w,'folder.user','folder@example.invalid','Folder','unused','member')"
        ),
        {"id": user, "w": workspace},
    )
    connection.execute(
        text("INSERT INTO folders(id,workspace_id,created_by,name) VALUES(:id,:w,:u,'Test')"),
        {"id": folder, "w": workspace, "u": user},
    )
    with pytest.raises(RuntimeError, match="Refusing downgrade with folder data"):
        command.downgrade(config, "20261103_rag04")
    assert connection.execute(text("SELECT id FROM folders")).scalar() == folder
