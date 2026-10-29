import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import JobStatus


class Meeting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Trạng thái xử lý nằm ở processing_jobs, không lặp lại ở đây."""

    __tablename__ = "meetings"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(300))
    meeting_date: Mapped[date] = mapped_column(Date)
    audio_storage_key: Mapped[str] = mapped_column(String(255))
    audio_content_type: Mapped[str] = mapped_column(String(100))
    audio_size_bytes: Mapped[int] = mapped_column(BigInteger)
    duration_sec: Mapped[float | None] = mapped_column(Float)
    summary_json: Mapped[dict | None] = mapped_column(JSONB)


class TranscriptSegment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "transcript_segments"
    __table_args__ = (UniqueConstraint("meeting_id", "segment_index"),)

    meeting_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"))
    segment_index: Mapped[int] = mapped_column(Integer)
    start_sec: Mapped[float] = mapped_column(Float)
    end_sec: Mapped[float] = mapped_column(Float)
    text: Mapped[str] = mapped_column(Text)


class ActionItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Candidate do AI trích xuất; chưa phải task."""

    __tablename__ = "action_items"

    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    assignee_name: Mapped[str | None] = mapped_column(String(200))
    due_date: Mapped[date | None] = mapped_column(Date)
    needs_review: Mapped[bool] = mapped_column(default=True)
    evidence_json: Mapped[list] = mapped_column(JSONB, default=list)
    confidence_note: Mapped[str | None] = mapped_column(Text)


class ProcessingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Hàng đợi job nặng; worker nhận job bằng FOR UPDATE SKIP LOCKED (ADR-05)."""

    __tablename__ = "processing_jobs"
    __table_args__ = (
        Index("ix_processing_jobs_status_created_at", "status", "created_at"),
        Index("ix_processing_jobs_entity", "entity_type", "entity_id"),
    )

    entity_type: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[uuid.UUID]
    status: Mapped[JobStatus] = mapped_column(
        str_enum(JobStatus, "job_status"), default=JobStatus.QUEUED
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
