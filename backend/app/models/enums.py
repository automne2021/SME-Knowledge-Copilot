"""Mỗi entity có enum trạng thái riêng (spec mục 6.5)."""

from enum import StrEnum


class UserRole(StrEnum):
    MEMBER = "member"
    KNOWLEDGE_ADMIN = "knowledge_admin"
    APPROVER = "approver"
    DEMO_ADMIN = "demo_admin"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRY_WAIT = "retry_wait"
    CANCELLED = "cancelled"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    NEEDS_OCR = "needs_ocr"
    DELETING = "deleting"
    DELETED = "deleted"


class RevisionStatus(StrEnum):
    STAGING = "staging"
    READY = "ready"
    FAILED = "failed"
    RETIRED = "retired"


class RagJobKind(StrEnum):
    INGEST = "ingest"
    CLEANUP = "cleanup"


class QueryStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class AnswerStatus(StrEnum):
    GROUNDED = "grounded"
    PARTIAL = "partial"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


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
