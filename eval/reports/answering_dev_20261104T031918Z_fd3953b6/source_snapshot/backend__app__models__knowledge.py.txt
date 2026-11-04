"""RAG metadata contracts. Worker/index/answer behavior is implemented in later steps."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import AnswerStatus, DocumentStatus, MessageRole, QueryStatus, RevisionStatus


class AuthToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auth_tokens"
    __table_args__ = (
        CheckConstraint("token_hash ~ '^[0-9a-f]{64}$'", name="hash_format"),
        CheckConstraint("expires_at > created_at", name="expiry_order"),
        Index("ix_auth_tokens_expiry", "expires_at"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        ForeignKeyConstraint(
            ["created_by", "workspace_id"],
            ["users.id", "users.workspace_id"],
            name="fk_documents_creator_scope",
        ),
        ForeignKeyConstraint(
            ["active_revision_id", "id"],
            ["document_revisions.id", "document_revisions.document_id"],
            name="fk_documents_active_revision",
            use_alter=True,
        ),
        CheckConstraint("size_bytes >= 0", name="size_nonnegative"),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="hash_format"),
        CheckConstraint("length(btrim(filename)) > 0", name="filename_nonempty"),
        CheckConstraint("lifecycle_version >= 1", name="lifecycle_positive"),
        CheckConstraint(
            "(active_revision_id IS NULL) = (active_generation_id IS NULL)", name="active_pair"
        ),
        CheckConstraint("status <> 'ready' OR active_revision_id IS NOT NULL", name="ready_active"),
        CheckConstraint("status <> 'deleted' OR deleted_at IS NOT NULL", name="deleted_timestamp"),
        Index(
            "uq_documents_workspace_hash_live",
            "workspace_id",
            "sha256",
            unique=True,
            postgresql_where=text("status <> 'deleted'"),
        ),
        Index(
            "ix_documents_workspace_status_created", "workspace_id", "status", "created_at", "id"
        ),
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    created_by: Mapped[uuid.UUID]
    filename: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[DocumentStatus] = mapped_column(
        str_enum(DocumentStatus, "document_status"), default=DocumentStatus.QUEUED
    )
    active_revision_id: Mapped[uuid.UUID | None]
    active_generation_id: Mapped[uuid.UUID | None]
    lifecycle_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    warnings_json: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentRevision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_revisions"
    __table_args__ = (
        UniqueConstraint("document_id", "version"),
        UniqueConstraint("id", "document_id", name="uq_revisions_id_document"),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint("expected_chunk_count >= 0", name="chunk_count_nonnegative"),
    )
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[RevisionStatus] = mapped_column(
        str_enum(RevisionStatus, "revision_status"), default=RevisionStatus.STAGING
    )
    storage_key: Mapped[str] = mapped_column(String(500))
    parser_version: Mapped[str] = mapped_column(String(100), default="pending")
    chunking_config: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    embedding_fingerprint: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    index_version: Mapped[str] = mapped_column(String(128), default="pending")
    collection_name: Mapped[str] = mapped_column(String(128), default="pending")
    expected_chunk_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class SourceBlock(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_blocks"
    __table_args__ = (
        UniqueConstraint("revision_id", "generation_id", "block_index"),
        CheckConstraint("block_index >= 0", name="block_index_nonnegative"),
    )
    revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_revisions.id"))
    generation_id: Mapped[uuid.UUID]
    block_index: Mapped[int] = mapped_column(Integer)
    raw_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(Text)
    location_json: Mapped[dict] = mapped_column(JSONB)


class Chunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("revision_id", "generation_id", "chunk_index"),
        CheckConstraint("chunk_index >= 0 AND token_count >= 0", name="counts_nonnegative"),
        CheckConstraint("length(btrim(text)) > 0", name="text_nonempty"),
        CheckConstraint("text_sha256 ~ '^[0-9a-f]{64}$'", name="hash_format"),
    )
    revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_revisions.id"))
    generation_id: Mapped[uuid.UUID]
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    text_sha256: Mapped[str] = mapped_column(String(64))
    location_json: Mapped[dict] = mapped_column(JSONB)
    source_spans_json: Mapped[list] = mapped_column(JSONB)
    vector_point_id: Mapped[uuid.UUID] = mapped_column(unique=True)
    token_count: Mapped[int] = mapped_column(Integer)


class ChatSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["created_by", "workspace_id"],
            ["users.id", "users.workspace_id"],
            name="fk_chat_sessions_owner_scope",
        ),
        Index("ix_chat_sessions_owner_created", "workspace_id", "created_by", "created_at", "id"),
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    created_by: Mapped[uuid.UUID]
    title: Mapped[str] = mapped_column(String(200), default="Cuộc trò chuyện mới")


class QueryRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "query_runs"
    __table_args__ = (
        UniqueConstraint("session_id", "client_request_id"),
        UniqueConstraint("id", "session_id", name="uq_query_runs_id_session"),
        Index(
            "uq_query_runs_running_session",
            "session_id",
            unique=True,
            postgresql_where=text("status = 'running'"),
        ),
        CheckConstraint("input_hash ~ '^[0-9a-f]{64}$'", name="hash_format"),
        CheckConstraint("length(btrim(question)) BETWEEN 1 AND 4000", name="question_length"),
        CheckConstraint("deadline_at > started_at", name="deadline_order"),
    )
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_sessions.id"))
    client_request_id: Mapped[uuid.UUID]
    input_hash: Mapped[str] = mapped_column(String(64))
    question: Mapped[str] = mapped_column(Text)
    status: Mapped[QueryStatus] = mapped_column(
        str_enum(QueryStatus, "query_status"), default=QueryStatus.RUNNING
    )
    config_json: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    retrieval_trace_json: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    error_code: Mapped[str | None] = mapped_column(String(64))
    deadline_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC) + timedelta(seconds=90)
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["query_run_id", "session_id"],
            ["query_runs.id", "query_runs.session_id"],
            name="fk_messages_run_session",
        ),
        UniqueConstraint("query_run_id", "role"),
    )
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_sessions.id"))
    query_run_id: Mapped[uuid.UUID]
    role: Mapped[MessageRole] = mapped_column(str_enum(MessageRole, "message_role"))
    content: Mapped[str] = mapped_column(Text, default="")
    structured_answer_json: Mapped[dict | None] = mapped_column(JSONB)
    answer_status: Mapped[AnswerStatus | None] = mapped_column(
        str_enum(AnswerStatus, "answer_status")
    )
    source_unavailable: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class AnswerCitation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "answer_citations"
    __table_args__ = (
        UniqueConstraint("message_id", "evidence_id"),
        ForeignKeyConstraint(
            ["revision_id", "document_id"],
            ["document_revisions.id", "document_revisions.document_id"],
            name="fk_citations_revision_document",
        ),
        CheckConstraint("source_status IN ('available', 'unavailable')", name="source_status"),
    )
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_messages.id"))
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chunks.id", ondelete="SET NULL"))
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    revision_id: Mapped[uuid.UUID]
    generation_id: Mapped[uuid.UUID]
    evidence_id: Mapped[str] = mapped_column(String(32))
    location_snapshot: Mapped[dict] = mapped_column(JSONB)
    excerpt_snapshot: Mapped[str | None] = mapped_column(Text)
    source_status: Mapped[str] = mapped_column(
        String(32), default="available", server_default="available"
    )


class EvalRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "eval_runs"
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    dataset_version: Mapped[str] = mapped_column(String(100))
    corpus_version: Mapped[str] = mapped_column(String(100))
    git_commit: Mapped[str] = mapped_column(String(64))
    config_json: Mapped[dict] = mapped_column(JSONB)
    results_path: Mapped[str] = mapped_column(String(500))
