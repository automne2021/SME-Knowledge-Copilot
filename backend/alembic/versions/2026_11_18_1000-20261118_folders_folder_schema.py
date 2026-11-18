"""Workspace-scoped folders and nullable document classification.

Revision ID: 20261118_folders
Revises: 20261103_rag04
"""

import sqlalchemy as sa
from alembic import op

revision = "20261118_folders"
down_revision = "20261103_rag04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "folders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_folders")),
        sa.UniqueConstraint("id", "workspace_id", name="uq_folders_id_workspace"),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], name=op.f("fk_folders_workspace_id_workspaces")
        ),
        sa.ForeignKeyConstraint(
            ["created_by", "workspace_id"],
            ["users.id", "users.workspace_id"],
            name="fk_folders_creator_scope",
        ),
        sa.CheckConstraint(
            "length(btrim(name)) BETWEEN 1 AND 100", name=op.f("ck_folders_name_length")
        ),
        sa.CheckConstraint("name = btrim(name)", name=op.f("ck_folders_name_trimmed")),
    )
    op.create_index(
        "uq_folders_workspace_name_ci",
        "folders",
        ["workspace_id", sa.text("lower(name)")],
        unique=True,
    )
    op.add_column("documents", sa.Column("folder_id", sa.Uuid(), nullable=True))
    # Separate FKs let SET NULL change only folder_id, never the non-null workspace_id.
    op.create_foreign_key(
        op.f("fk_documents_folder_id_folders"),
        "documents",
        "folders",
        ["folder_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_documents_folder_scope",
        "documents",
        "folders",
        ["folder_id", "workspace_id"],
        ["id", "workspace_id"],
    )
    op.create_index("ix_documents_workspace_folder", "documents", ["workspace_id", "folder_id"])


def downgrade() -> None:
    if op.get_bind().execute(sa.text("SELECT EXISTS(SELECT 1 FROM folders)")).scalar():
        raise RuntimeError("Refusing downgrade with folder data; export/review explicitly")
    op.drop_index("ix_documents_workspace_folder", table_name="documents")
    op.drop_constraint("fk_documents_folder_scope", "documents", type_="foreignkey")
    op.drop_constraint(op.f("fk_documents_folder_id_folders"), "documents", type_="foreignkey")
    op.drop_column("documents", "folder_id")
    op.drop_index("uq_folders_workspace_name_ci", table_name="folders")
    op.drop_table("folders")
