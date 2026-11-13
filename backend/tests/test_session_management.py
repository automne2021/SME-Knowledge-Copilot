"""Real PostgreSQL/API contracts for logout and owner-only session rename/delete; no model calls."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.models import (
    AnswerCitation,
    AuthToken,
    ChatMessage,
    ChatSession,
    Chunk,
    DocumentRevision,
    QueryRun,
)
from tests.test_rag_identity import headers, make_document


def new_session(client, auth, title="Phiên thử"):
    response = client.post("/api/v1/chat/sessions", headers=auth, json={"title": title})
    assert response.status_code == 201
    return response.json()["data"]["id"]


def history(db, person, status="completed", deadline=None):
    """One answered turn with a citation, enough to prove delete removes every row."""
    doc = make_document(db, person)
    revision = DocumentRevision(
        document_id=doc.id, version=1, storage_key="k", status="ready", expected_chunk_count=1
    )
    db.add(revision)
    db.flush()
    generation = uuid.uuid4()
    chunk = Chunk(
        revision_id=revision.id,
        generation_id=generation,
        chunk_index=0,
        text="fact",
        text_sha256="a" * 64,
        location_json={},
        source_spans_json=[],
        vector_point_id=uuid.uuid4(),
        token_count=1,
    )
    doc.active_revision_id, doc.active_generation_id, doc.status = revision.id, generation, "ready"
    session = ChatSession(workspace_id=person.workspace_id, created_by=person.id)
    db.add_all([chunk, session])
    db.flush()
    now = datetime.now(UTC)
    run = QueryRun(
        session_id=session.id,
        client_request_id=uuid.uuid4(),
        input_hash="a" * 64,
        question="Câu hỏi",
        status=status,
        started_at=now - timedelta(seconds=5),
        deadline_at=deadline or now + timedelta(seconds=60),
    )
    db.add(run)
    db.flush()
    user_message = ChatMessage(
        session_id=session.id, query_run_id=run.id, role="user", content="Câu hỏi"
    )
    answer = ChatMessage(
        session_id=session.id,
        query_run_id=run.id,
        role="assistant",
        content="Trả lời",
        answer_status="grounded",
    )
    db.add_all([user_message, answer])
    db.flush()
    db.add(
        AnswerCitation(
            message_id=answer.id,
            chunk_id=chunk.id,
            document_id=doc.id,
            revision_id=revision.id,
            generation_id=generation,
            evidence_id="E1",
            location_snapshot={},
            excerpt_snapshot="excerpt",
        )
    )
    db.flush()
    return session, run


def counts(db, session_id):
    return (
        db.scalar(
            select(func.count()).select_from(ChatSession).where(ChatSession.id == session_id)
        ),
        db.scalar(
            select(func.count()).select_from(QueryRun).where(QueryRun.session_id == session_id)
        ),
        db.scalar(
            select(func.count())
            .select_from(ChatMessage)
            .where(ChatMessage.session_id == session_id)
        ),
        db.scalar(
            select(func.count())
            .select_from(AnswerCitation)
            .join(ChatMessage, AnswerCitation.message_id == ChatMessage.id)
            .where(ChatMessage.session_id == session_id)
        ),
    )


def test_logout_revokes_only_the_presented_token(client, db_session, people):
    first, second = headers(client, people["member"]), headers(client, people["member"])
    response = client.post("/api/v1/auth/logout", headers=first)
    assert response.status_code == 200
    assert response.json()["data"] == {"revoked": True}
    assert client.get("/api/v1/auth/me", headers=first).status_code == 401
    assert client.get("/api/v1/auth/me", headers=second).status_code == 200
    revoked = db_session.scalars(select(AuthToken).where(AuthToken.revoked_at.is_not(None))).all()
    assert len(revoked) == 1
    # A revoked, missing or malformed token cannot log out again.
    assert client.post("/api/v1/auth/logout", headers=first).status_code == 401
    assert client.post("/api/v1/auth/logout").status_code == 401
    bad = {"Authorization": "Bearer not-a-token"}
    assert client.post("/api/v1/auth/logout", headers=bad).status_code == 401


def test_owner_renames_session_and_title_is_validated(client, people):
    auth = headers(client, people["member"])
    session_id = new_session(client, auth)
    response = client.patch(
        f"/api/v1/chat/sessions/{session_id}", headers=auth, json={"title": "  Hoàn ứng  "}
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Hoàn ứng"
    listing = client.get("/api/v1/chat/sessions", headers=auth).json()["data"]["items"]
    assert [row["title"] for row in listing] == ["Hoàn ứng"]
    for body in [{"title": "   "}, {"title": "x" * 201}, {}, {"title": "a", "created_by": "x"}]:
        bad = client.patch(f"/api/v1/chat/sessions/{session_id}", headers=auth, json=body)
        assert bad.status_code == 422


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_session_changes_are_owner_only_including_admin(client, db_session, people, method):
    owner = headers(client, people["member"])
    session_id = new_session(client, owner, "Riêng tư")
    for person in ["admin", "other"]:
        auth = headers(client, people[person])
        kwargs = {"json": {"title": "Chiếm quyền"}} if method == "patch" else {}
        response = getattr(client, method)(
            f"/api/v1/chat/sessions/{session_id}", headers=auth, **kwargs
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"
    unknown = getattr(client, method)(
        f"/api/v1/chat/sessions/{uuid.uuid4()}",
        headers=owner,
        **({"json": {"title": "x"}} if method == "patch" else {}),
    )
    assert unknown.status_code == 404
    row = db_session.get(ChatSession, uuid.UUID(session_id), populate_existing=True)
    assert row is not None and row.title == "Riêng tư"


def test_delete_removes_whole_history(client, db_session, people):
    person = people["member"]
    session, run = history(db_session, person)
    session_id, run_id = session.id, run.id
    auth = headers(client, person)
    assert counts(db_session, session_id) == (1, 1, 2, 1)
    response = client.delete(f"/api/v1/chat/sessions/{session_id}", headers=auth)
    assert response.status_code == 200
    assert response.json()["data"] == {"id": str(session_id), "deleted": True}
    db_session.expire_all()
    assert counts(db_session, session_id) == (0, 0, 0, 0)
    assert client.get("/api/v1/chat/sessions", headers=auth).json()["data"]["items"] == []
    assert client.get(f"/api/v1/chat/runs/{run_id}", headers=auth).status_code == 404
    gone = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=auth)
    assert gone.status_code == 404
    assert client.delete(f"/api/v1/chat/sessions/{session_id}", headers=auth).status_code == 404


def test_delete_is_refused_while_a_query_is_running(client, db_session, people):
    person = people["member"]
    session, run = history(db_session, person, status="running")
    auth = headers(client, person)
    response = client.delete(f"/api/v1/chat/sessions/{session.id}", headers=auth)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "session_busy"
    assert response.json()["error"]["details"] == {"run_id": str(run.id)}
    db_session.expire_all()
    assert counts(db_session, session.id) == (1, 1, 2, 1)


def test_delete_expires_a_stale_running_query_first(client, db_session, people):
    person = people["member"]
    past = datetime.now(UTC) - timedelta(seconds=1)
    session, _ = history(db_session, person, status="running", deadline=past)
    session_id = session.id
    auth = headers(client, person)
    assert client.delete(f"/api/v1/chat/sessions/{session_id}", headers=auth).status_code == 200
    db_session.expire_all()
    assert counts(db_session, session_id) == (0, 0, 0, 0)


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_session_changes_require_identity(client, method):
    kwargs = {"json": {"title": "x"}} if method == "patch" else {}
    response = getattr(client, method)(f"/api/v1/chat/sessions/{uuid.uuid4()}", **kwargs)
    assert response.status_code == 401
