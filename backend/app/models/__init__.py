"""Import mọi model để Base.metadata đầy đủ (Alembic autogenerate dựa vào đây).

Giữ cả legacy Operations và RAG metadata, không để autogenerate drop bảng lịch sử.
"""

from app.models.audit import AuditEvent
from app.models.base import Base
from app.models.knowledge import (
    AnswerCitation,
    AuthToken,
    ChatMessage,
    ChatSession,
    Chunk,
    Document,
    DocumentRevision,
    EvalRun,
    Folder,
    QueryRun,
    SourceBlock,
)
from app.models.meeting import ActionItem, Meeting, ProcessingJob, TranscriptSegment
from app.models.task import Task, TaskProposal
from app.models.workspace import Project, ProjectMember, User, Workspace

__all__ = [
    "ActionItem",
    "AuditEvent",
    "Base",
    "Meeting",
    "ProcessingJob",
    "Project",
    "ProjectMember",
    "Task",
    "TaskProposal",
    "TranscriptSegment",
    "User",
    "Workspace",
    "AnswerCitation",
    "AuthToken",
    "ChatMessage",
    "ChatSession",
    "Chunk",
    "Document",
    "DocumentRevision",
    "EvalRun",
    "Folder",
    "QueryRun",
    "SourceBlock",
]
