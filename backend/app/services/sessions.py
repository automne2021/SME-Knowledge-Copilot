"""Owner-only chat session management: rename and hard delete.

Delete removes the session's history for good (citations, messages, runs, session) in one
transaction. It is refused while a query is still running, so a late publish can never
write into a session that no longer exists.
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import AnswerCitation, ChatMessage, ChatSession, QueryRun, User
from app.services.access import session_for_user
from app.services.chat import expire_runs


def busy(run_id=None) -> AppError:
    details = {"run_id": str(run_id)} if run_id else {}
    return AppError(409, "session_busy", "Cuộc trò chuyện đang xử lý một câu hỏi.", details)


def lock_owned_session(db: Session, session_id: uuid.UUID, user: User) -> ChatSession:
    # Scope first (404 for foreign/missing), then the same NOWAIT lock used by query start
    # and publish, so rename/delete never wait behind an in-flight answer.
    session_for_user(db, session_id, user)
    try:
        return db.scalar(
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .with_for_update(nowait=True)
            .execution_options(populate_existing=True)
        )
    except OperationalError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) == "55P03":
            raise busy() from None
        raise


def rename_session(db: Session, session_id: uuid.UUID, user: User, title: str) -> ChatSession:
    row = lock_owned_session(db, session_id, user)
    row.title = title
    db.commit()
    return row


def delete_session(db: Session, session_id: uuid.UUID, user: User) -> None:
    lock_owned_session(db, session_id, user)
    expire_runs(db, session_id)
    active = db.scalar(
        select(QueryRun.id).where(QueryRun.session_id == session_id, QueryRun.status == "running")
    )
    if active:
        db.commit()
        raise busy(active)
    messages = select(ChatMessage.id).where(ChatMessage.session_id == session_id)
    db.execute(delete(AnswerCitation).where(AnswerCitation.message_id.in_(messages)))
    db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    db.execute(delete(QueryRun).where(QueryRun.session_id == session_id))
    db.execute(delete(ChatSession).where(ChatSession.id == session_id))
    db.commit()
