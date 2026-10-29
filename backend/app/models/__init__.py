"""Import mọi model để Base.metadata đầy đủ (Alembic autogenerate dựa vào đây).

Schema hiện tại là phạm vi M1. Bảng M2 (documents, document_chunks, agent_runs,
tool_events) sẽ thêm bằng migration riêng.
"""

from app.models.audit import AuditEvent
from app.models.base import Base
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
]
