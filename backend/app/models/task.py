import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import ProposalOrigin, ProposalStatus, TaskStatus


class TaskProposal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Đề xuất chờ duyệt. Task tương ứng tìm qua tasks.proposal_id (quan hệ 1-1)."""

    __tablename__ = "task_proposals"
    __table_args__ = (
        # Mỗi action item có tối đa một proposal đang chờ duyệt (NFR-11).
        Index(
            "uq_task_proposals_pending_action_item",
            "source_action_item_id",
            unique=True,
            postgresql_where=text(
                "status = 'pending_approval' AND source_action_item_id IS NOT NULL"
            ),
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    origin: Mapped[ProposalOrigin] = mapped_column(str_enum(ProposalOrigin, "proposal_origin"))
    source_action_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("action_items.id"))
    payload_json: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[ProposalStatus] = mapped_column(
        str_enum(ProposalStatus, "proposal_status"), default=ProposalStatus.PENDING_APPROVAL
    )
    # Optimistic concurrency: client gửi version khi sửa/duyệt, lệch thì 409.
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Task chính thức. proposal_id NOT NULL + UNIQUE: task chỉ sinh ra từ một proposal đã duyệt."""

    __tablename__ = "tasks"
    __table_args__ = (
        # Mỗi action item sinh tối đa một task.
        Index(
            "uq_tasks_source_action_item",
            "source_action_item_id",
            unique=True,
            postgresql_where=text("source_action_item_id IS NOT NULL"),
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    proposal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("task_proposals.id"), unique=True)
    source_action_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("action_items.id"))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    assignee_name: Mapped[str | None] = mapped_column(String(200))
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[TaskStatus] = mapped_column(
        str_enum(TaskStatus, "task_status"), default=TaskStatus.TODO
    )
