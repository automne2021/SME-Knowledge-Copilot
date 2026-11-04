"""Real PostgreSQL query state; deterministic retrieval/provider fakes unless stated."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.db import get_db
from app.core.security import hash_password
from app.main import create_app
from app.models import (
    AnswerCitation,
    AuthToken,
    ChatMessage,
    ChatSession,
    Chunk,
    Document,
    DocumentRevision,
    QueryRun,
    User,
)
from tests.test_answering import FakeProvider


@pytest.fixture
def chat_env(worker_env, monkeypatch):
    env = worker_env
    with env.sessions() as db:
        user = db.get(User, env.user.id)
        user.password_hash = hash_password("chat-test-only-password")
        username = user.username
        db.commit()
    app = create_app()

    def sessions():
        with env.sessions() as db:
            yield db

    app.dependency_overrides[get_db] = sessions
    env.provider = FakeProvider()
    app.state.provider_factory = lambda settings: env.provider

    def fake_search(db, user, payload, settings, factory, deadline=None):
        from app.services.chat import source_state

        rows = db.execute(
            select(Chunk, Document)
            .join(DocumentRevision, Chunk.revision_id == DocumentRevision.id)
            .join(Document, Document.id == DocumentRevision.document_id)
            .where(Document.workspace_id == user.workspace_id, Document.status == "ready")
        ).all()
        hits = [
            {
                "chunk_id": str(chunk.id),
                "document_id": str(doc.id),
                "revision_id": str(chunk.revision_id),
                "generation_id": str(chunk.generation_id),
                "excerpt": chunk.text,
                "score": 1.0,
            }
            for chunk, doc in rows
        ]
        hits = source_state(db, user, hits)
        db.commit()
        return {
            "hits": hits,
            "reason_code": None if hits else "no_ready_documents",
            "trace": {"test_fake": True},
            "timings_ms": {"total": 1},
        }

    monkeypatch.setattr("app.services.chat.search", fake_search)
    with TestClient(app) as client:
        env.client, env.app = client, app
        response = client.post(
            "/api/v1/auth/login", json={"username": username, "password": "chat-test-only-password"}
        )
        env.auth = {"Authorization": "Bearer " + response.json()["data"]["access_token"]}
        session = client.post("/api/v1/chat/sessions", headers=env.auth, json={}).json()["data"][
            "id"
        ]
        env.payload = {
            "session_id": session,
            "client_request_id": str(uuid.uuid4()),
            "question": "policy",
        }
        env.ask = lambda **kwargs: client.post(
            "/api/v1/chat/query", headers=env.auth, json=env.payload | kwargs
        )
        try:
            yield env
        finally:
            with env.sessions() as db:
                session_ids = select(ChatSession.id).where(
                    ChatSession.workspace_id == env.user.workspace_id
                )
                message_ids = select(ChatMessage.id).where(ChatMessage.session_id.in_(session_ids))
                db.execute(delete(AnswerCitation).where(AnswerCitation.message_id.in_(message_ids)))
                db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(session_ids)))
                db.execute(delete(QueryRun).where(QueryRun.session_id.in_(session_ids)))
                db.execute(delete(ChatSession).where(ChatSession.id.in_(session_ids)))
                db.execute(delete(AuthToken).where(AuthToken.user_id == env.user.id))
                db.commit()


def ready(env, text=b"Policy condition."):
    value = env.upload(text)
    assert env.worker().run_once()["status"] == "completed"
    return value
