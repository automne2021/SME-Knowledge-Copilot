"""Ràng buộc DB là chốt chặn cuối cho các bất biến nghiệp vụ (spec 7.3, CLAUDE.md)."""

import uuid
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ActionItem, Meeting, Project, Task, TaskProposal, User, Workspace
from app.models.enums import ProposalOrigin, ProposalStatus, UserRole


@pytest.fixture
def action_item(db_session: Session) -> ActionItem:
    workspace = Workspace(name="Demo")
    db_session.add(workspace)
    db_session.flush()
    user = User(
        workspace_id=workspace.id,
        email=f"{uuid.uuid4().hex}@example.com",
        display_name="Approver",
        password_hash="not-a-real-hash",
        role=UserRole.APPROVER,
    )
    project = Project(workspace_id=workspace.id, name="ABC")
    db_session.add_all([user, project])
    db_session.flush()
    meeting = Meeting(
        project_id=project.id,
        created_by=user.id,
        title="Kickoff",
        meeting_date=date(2026, 10, 29),
        audio_storage_key="test.wav",
        audio_content_type="audio/wav",
        audio_size_bytes=1,
    )
    db_session.add(meeting)
    db_session.flush()
    item = ActionItem(meeting_id=meeting.id, title="Gửi thiết kế")
    db_session.add(item)
    db_session.flush()
    return item


def _proposal(item: ActionItem, status: ProposalStatus = ProposalStatus.PENDING_APPROVAL):
    session = Session.object_session(item)
    meeting = session.get(Meeting, item.meeting_id)
    return TaskProposal(
        project_id=meeting.project_id,
        origin=ProposalOrigin.PIPELINE,
        source_action_item_id=item.id,
        payload_json={"title": item.title},
        status=status,
        created_by=meeting.created_by,
    )


def _task(proposal: TaskProposal, source_action_item_id: uuid.UUID | None) -> Task:
    return Task(
        project_id=proposal.project_id,
        proposal_id=proposal.id,
        source_action_item_id=source_action_item_id,
        title="Gửi thiết kế",
    )


def _assert_rejected_by_db(db_session: Session, obj: object) -> None:
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(obj)
        db_session.flush()


def test_only_one_pending_proposal_per_action_item(
    db_session: Session, action_item: ActionItem
) -> None:
    db_session.add(_proposal(action_item))
    db_session.flush()

    _assert_rejected_by_db(db_session, _proposal(action_item))


def test_new_pending_proposal_allowed_after_rejection(
    db_session: Session, action_item: ActionItem
) -> None:
    db_session.add(_proposal(action_item, ProposalStatus.REJECTED))
    db_session.flush()

    db_session.add(_proposal(action_item))
    db_session.flush()


def test_task_requires_a_proposal(db_session: Session, action_item: ActionItem) -> None:
    proposal = _proposal(action_item)
    db_session.add(proposal)
    db_session.flush()
    task = _task(proposal, None)
    task.proposal_id = None

    _assert_rejected_by_db(db_session, task)


def test_one_task_per_proposal(db_session: Session, action_item: ActionItem) -> None:
    proposal = _proposal(action_item, ProposalStatus.EXECUTED)
    db_session.add(proposal)
    db_session.flush()
    db_session.add(_task(proposal, None))
    db_session.flush()

    _assert_rejected_by_db(db_session, _task(proposal, None))


def test_one_task_per_action_item(db_session: Session, action_item: ActionItem) -> None:
    first = _proposal(action_item, ProposalStatus.EXECUTED)
    second = _proposal(action_item, ProposalStatus.EXECUTED)
    db_session.add_all([first, second])
    db_session.flush()
    db_session.add(_task(first, action_item.id))
    db_session.flush()

    _assert_rejected_by_db(db_session, _task(second, action_item.id))


def test_unknown_proposal_status_rejected(db_session: Session, action_item: ActionItem) -> None:
    proposal = _proposal(action_item)
    db_session.add(proposal)
    db_session.flush()

    # Không có trạng thái "approved" (ADR-10); CHECK constraint chặn ngay cả SQL thô.
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(
            text("UPDATE task_proposals SET status = 'approved' WHERE id = :id"),
            {"id": proposal.id},
        )
