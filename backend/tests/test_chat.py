"""Real PostgreSQL query state; deterministic retrieval/provider fakes unless stated."""

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.core.errors import AppError
from app.models import (
    ChatMessage,
    ChatSession,
    Document,
    QueryRun,
    User,
)
from tests.chat_support import ready
from tests.test_answering import FakeProvider, output


def test_no_sources_abstains_without_provider_and_replays(chat_env):
    env = chat_env
    response = env.ask()
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert (
        data["answer_status"] == "insufficient_evidence"
        and data["reason_code"] == "no_ready_documents"
    )
    assert not env.provider.calls and not env.provider.counts
    assert env.ask().json()["data"]["message_id"] == data["message_id"]
    with env.sessions() as db:
        assert len(db.scalars(select(ChatMessage)).all()) == 2


def test_grounded_trusted_citations_and_unchanged_replay(chat_env):
    env = chat_env
    ready(env)

    # No open transaction / row locks during provider inference.
    def unlocked():
        with env.sessions() as db:
            db.scalars(
                select(Document)
                .where(Document.workspace_id == env.user.workspace_id)
                .with_for_update(nowait=True)
            ).all()
            db.scalar(
                select(ChatSession)
                .where(ChatSession.id == uuid.UUID(env.payload["session_id"]))
                .with_for_update(nowait=True)
            )

    env.provider.callback = unlocked
    response = env.ask()
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["answer"].endswith("[E1]") and len(data["citations"]) == 1
    citation = data["citations"][0]
    assert citation["file_name"] == "source.txt" and citation["excerpt"] == "Policy condition."
    assert citation["document_version"] == 1 and citation["location"]["kind"] == "line_range"
    assert env.ask().json()["data"] == data
    assert len(env.provider.calls) == 1
    history = env.client.get(
        f"/api/v1/chat/sessions/{env.payload['session_id']}/messages", headers=env.auth
    ).json()["data"]["items"]
    assert history[-1]["answer"]["citations"] == data["citations"]
    with env.sessions() as db:
        run = db.get(QueryRun, uuid.UUID(data["run_id"]))
        assert (
            run.status == "completed"
            and run.retrieval_trace_json["evidence_map"][0]["source_spans"]
        )


@pytest.mark.parametrize(
    "outputs,code",
    [
        (["{bad"], "invalid_model_output"),
        ([output(ids=["E99"])], "invalid_model_output"),
        ([AppError(503, "model_unavailable", "safe")], "model_unavailable"),
        ([AppError(504, "model_timeout", "safe")], "model_timeout"),
    ],
)
def test_errors_do_not_publish_assistant_or_retry_failed_id(chat_env, outputs, code):
    env = chat_env
    ready(env)
    env.provider = FakeProvider(outputs)
    response = env.ask()
    assert response.json()["error"]["code"] == code, response.text
    count = len(env.provider.calls)
    assert env.ask().json()["error"]["code"] == code and len(env.provider.calls) == count
    with env.sessions() as db:
        assert db.scalar(select(QueryRun)).status == "failed"
        assert list(db.scalars(select(ChatMessage.role))) == ["user"]


def test_repair_once_then_success_and_citation_from_final_context_only(chat_env, monkeypatch):
    env = chat_env
    ready(env)
    env.provider = FakeProvider([output(ids=["E2"]), output()])
    response = env.ask()
    assert response.status_code == 200 and len(env.provider.calls) == 2
    assert env.provider.calls[0]["contents"] == env.provider.calls[1]["contents"]


def test_partial_conflict_and_model_abstention_has_no_free_form_claims(chat_env):
    env = chat_env
    ready(env)
    ready(env, b"Conflicting policy.")
    value = output("partial", ["E1", "E2"]) | {
        "limitations": ["Both versions conflict."],
        "conflict_detected": True,
    }
    env.provider = FakeProvider([value])
    result = env.ask().json()["data"]
    assert result["answer_status"] == "partial" and len(result["citations"]) == 2
    env.provider = FakeProvider(
        [output("insufficient_evidence") | {"claims": [], "limitations": ["untrusted explanation"]}]
    )
    result = env.ask(client_request_id=str(uuid.uuid4())).json()["data"]
    assert (
        result["limitations"] == []
        and result["citations"] == []
        and "untrusted" not in result["answer"]
    )


def test_all_chunks_budget_excluded_does_not_generate(chat_env, monkeypatch):
    env = chat_env
    ready(env)
    monkeypatch.setattr(get_settings(), "llm_evidence_budget_tokens", 1)
    result = env.ask().json()["data"]
    assert result["reason_code"] == "context_budget_excluded" and not env.provider.calls


def test_source_changes_during_generation_fail_and_replay_is_redacted(chat_env):
    env = chat_env
    uploaded = ready(env)
    doc_id = uploaded["document_id"]

    def changed():
        with env.sessions() as db:
            db.get(Document, doc_id).status = "deleting"
            db.commit()

    env.provider.callback = changed
    response = env.ask()
    assert response.json()["error"]["code"] == "source_changed", response.text
    with env.sessions() as db:
        db.get(Document, doc_id).status = "ready"
        db.commit()
    env.provider.callback = None
    payload_id = str(uuid.uuid4())
    result = env.ask(client_request_id=payload_id).json()["data"]
    changed()
    for response in [
        env.ask(client_request_id=payload_id),
        env.client.get("/api/v1/chat/runs/" + result["run_id"], headers=env.auth),
    ]:
        data = response.json()["data"]
        assert data["source_unavailable"] and data["answer"] == "" and data["citations"] == []
        assert "Policy condition" not in response.text
    history = env.client.get(
        f"/api/v1/chat/sessions/{env.payload['session_id']}/messages", headers=env.auth
    )
    assert "Policy condition" not in history.text
    assert history.json()["data"]["items"][-1]["answer"] is None


def test_lost_commit_ack_replays_persisted_answer_without_second_call(chat_env, monkeypatch):
    env = chat_env
    ready(env)
    from sqlalchemy.orm import Session

    original = Session.commit
    fired = []

    def commit(db):
        completed = any(isinstance(row, QueryRun) and row.status == "completed" for row in db.dirty)
        result = original(db)
        if completed and not fired:
            fired.append(True)
            raise OperationalError("test-only", {}, Exception("ack lost"))
        return result

    monkeypatch.setattr(Session, "commit", commit)
    assert env.ask().status_code == 503 and fired
    assert env.ask().status_code == 200 and len(env.provider.calls) == 1


def test_owner_scope_even_admin_cannot_query_another_members_session(chat_env):
    env = chat_env
    # The same user's session in a different workspace is impossible via the composite FK.
    # Create a second member in this workspace to verify the stronger owner restriction.
    new_user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    with env.sessions() as db:
        db.add(
            User(
                id=new_user_id,
                workspace_id=env.user.workspace_id,
                username="s8-test." + new_user_id.hex,
                email=new_user_id.hex + "@example.invalid",
                display_name="other member",
                role="member",
                password_hash="unused",
            )
        )
        db.flush()
        db.add(
            ChatSession(id=session_id, workspace_id=env.user.workspace_id, created_by=new_user_id)
        )
        db.commit()
    try:
        assert env.ask(session_id=str(session_id)).status_code == 404
        assert (
            env.client.get(
                f"/api/v1/chat/sessions/{session_id}/messages", headers=env.auth
            ).status_code
            == 404
        )
    finally:
        with env.sessions() as db:
            db.execute(delete(ChatSession).where(ChatSession.id == session_id))
            db.execute(delete(User).where(User.id == new_user_id))
            db.commit()


def test_idempotency_input_owner_and_strict_validation(chat_env):
    env = chat_env
    assert env.ask().status_code == 200
    assert env.ask(question="other").json()["error"]["code"] == "idempotency_conflict"
    assert env.ask(session_id=str(uuid.uuid4())).status_code == 404
    for change in [
        {"oracle_context": []},
        {"question": 5},
        {"question": " "},
        {"top_k": True},
        {"retrieval_mode": "hybrid"},
    ]:
        assert env.ask(**change).status_code == 422
    assert env.client.post("/api/v1/chat/query", json=env.payload).status_code == 401


def test_in_progress_busy_cross_session_and_deadline_recovery(chat_env):
    env = chat_env
    ready(env)
    entered, release = threading.Event(), threading.Event()
    env.provider.callback = lambda: (entered.set(), release.wait(20))
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(env.ask)
        try:
            assert entered.wait(15)
            assert env.ask().json()["error"]["code"] == "query_in_progress"
            assert (
                env.ask(client_request_id=str(uuid.uuid4())).json()["error"]["code"]
                == "session_busy"
            )
            session2 = env.client.post("/api/v1/chat/sessions", headers=env.auth, json={}).json()[
                "data"
            ]["id"]
            old = env.provider
            env.provider = FakeProvider()
            assert env.ask(session_id=session2).status_code == 200
            env.provider = old
            with env.sessions() as db:
                row = db.scalar(
                    select(QueryRun).where(
                        QueryRun.session_id == uuid.UUID(env.payload["session_id"])
                    )
                )
                row.started_at = datetime.now(UTC) - timedelta(seconds=20)
                row.deadline_at = datetime.now(UTC) - timedelta(seconds=1)
                run_id = str(row.id)
                db.commit()
            expired = env.client.get("/api/v1/chat/runs/" + run_id, headers=env.auth).json()["data"]
            assert expired["status"] == "failed" and expired["error_code"] == "model_timeout"
        finally:
            release.set()
        assert future.result(timeout=15).status_code == 504


def test_capacity_and_total_deadline_release_session(chat_env, monkeypatch):
    env = chat_env
    ready(env)
    env.app.state.llm_capacity = threading.BoundedSemaphore(1)
    env.app.state.llm_capacity.acquire()
    try:
        assert env.ask().status_code == 429
    finally:
        env.app.state.llm_capacity.release()
    monkeypatch.setattr(get_settings(), "query_timeout_seconds", 0.1)
    env.provider.callback = lambda: time.sleep(0.15)
    response = env.ask(client_request_id=str(uuid.uuid4()))
    assert response.status_code == 504, response.text


def test_database_publish_failure_returns_error_without_assistant(chat_env, monkeypatch):
    env = chat_env
    ready(env)
    from sqlalchemy.orm import Session

    original = Session.commit
    fired = []

    def commit(db):
        if not fired and any(
            isinstance(row, QueryRun) and row.status == "completed" for row in db.dirty
        ):
            fired.append(True)
            raise OperationalError("test-only", {}, Exception("no commit"))
        return original(db)

    monkeypatch.setattr(Session, "commit", commit)
    response = env.ask()
    assert response.status_code == 503 and fired
    with env.sessions() as db:
        assert list(db.scalars(select(ChatMessage.role))) == ["user"]


def test_production_search_path_remains_available_with_llm_disabled(chat_env, monkeypatch):
    env = chat_env
    ready(env)
    from app.services.retrieval import search

    monkeypatch.setattr("app.services.chat.search", search)

    class QueryEmbedder:
        def encode_query(self, query, deadline=None):
            return [1.0] + [0.0] * 383

    env.app.state.search_runtime = SimpleNamespace(
        profile=env.profile,
        vector=env.vector,
        embedder=QueryEmbedder(),
        counter=SimpleNamespace(count_query=lambda text: 10),
        lock=threading.Lock(),
        close=lambda: None,
    )
    assert env.ask().status_code == 200
