"""Mỗi entity có enum trạng thái riêng (spec mục 6.5)."""

from enum import StrEnum


class UserRole(StrEnum):
    MEMBER = "member"
    APPROVER = "approver"
    DEMO_ADMIN = "demo_admin"


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProposalStatus(StrEnum):
    PENDING_APPROVAL = "pending_approval"
    EXECUTED = "executed"
    REJECTED = "rejected"


class ProposalOrigin(StrEnum):
    PIPELINE = "pipeline"
    AGENT = "agent"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
