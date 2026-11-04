"""Real SQL/Qdrant and controlled delete races; no paid calls or model inference."""

import json
import logging
import os
import subprocess
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.models import (
    AnswerCitation,
    ChatMessage,
    Chunk,
    Document,
    DocumentRevision,
    ProcessingJob,
    QueryRun,
    SourceBlock,
    User,
    Workspace,
)
from app.services.cleanup import CleanupQueue, CleanupWorker
from app.services.deletion import delete_document, retry_cleanup
from app.services.vectors import QdrantIndex
from app.services.worker_errors import LeaseLost, WorkerError
from tests.chat_support import ready


def cleanup(env):
    return CleanupWorker(CleanupQueue(env.sessions, env.settings), env.vector)


def remove(env, document_id):
    with env.sessions() as db:
        return delete_document(db, document_id, env.user)


def doc_state(env, document_id):
    with env.sessions() as db:
        return db.get(Document, document_id)


def make_due(env, job_id, expired=False):
    with env.sessions() as db:
        row = db.get(ProcessingJob, job_id)
        if expired:
            row.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
        else:
            row.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()


def test_delete_ready_hides_source_then_cleans_all_layers_and_reupload(chat_env):
    env = chat_env
    uploaded = ready(env, b"S9 confidential policy.")
    doc_id = uploaded["document_id"]
    answer = env.ask().json()["data"]
    citation = answer["citations"][0]
    with env.sessions() as db:
        run = db.get(QueryRun, uuid.UUID(answer["run_id"]))
        assert "S9 confidential" not in json.dumps(run.retrieval_trace_json)
        assert "excerpt" not in run.retrieval_trace_json["evidence_map"][0]
        file = (
            env.settings.storage_dir
            / db.get(DocumentRevision, uuid.UUID(citation["revision_id"])).storage_key
        )
    path = f"/api/v1/documents/{doc_id}"
    response = env.client.delete(path, headers=env.auth)
    assert response.status_code == 202, response.text
    assert (
        env.client.delete(path, headers=env.auth).json()["data"]["job_id"]
        == response.json()["data"]["job_id"]
    )
    assert env.client.get(citation["chunk_url"], headers=env.auth).status_code == 410
    assert env.client.get(citation["content_url"], headers=env.auth).status_code == 410
    search = env.client.post("/api/v1/search", headers=env.auth, json={"query": "policy"})
    assert search.status_code == 200 and search.json()["data"]["hits"] == []
    replay = env.ask().json()["data"]
    assert replay["source_unavailable"] and replay["answer"] == "" and replay["citations"] == []
    after = env.ask(client_request_id=str(uuid.uuid4())).json()["data"]
    assert after["answer_status"] == "insufficient_evidence"
    assert cleanup(env).run_once()["status"] == "completed"
    assert not file.exists() and doc_state(env, doc_id).status == "deleted"
    assert not env.vector.document_points(env.user.workspace_id, doc_id)
    assert env.client.delete(path, headers=env.auth).status_code == 200
    with env.sessions() as db:
        revisions = list(
            db.scalars(select(DocumentRevision).where(DocumentRevision.document_id == doc_id))
        )
        ids = [row.id for row in revisions]
        assert all(row.storage_key == "" and row.status == "retired" for row in revisions)
        assert not list(db.scalars(select(Chunk).where(Chunk.revision_id.in_(ids))))
        assert not list(db.scalars(select(SourceBlock).where(SourceBlock.revision_id.in_(ids))))
        message = db.get(ChatMessage, uuid.UUID(answer["message_id"]))
        assert (
            message.content == ""
            and message.structured_answer_json is None
            and message.source_unavailable
        )
        source = db.scalar(select(AnswerCitation).where(AnswerCitation.message_id == message.id))
        assert (
            source.chunk_id is None
            and source.excerpt_snapshot is None
            and source.location_snapshot == {}
        )
        assert source.source_status == "unavailable"
    assert env.upload(b"S9 confidential policy.")["document_id"] != doc_id


@pytest.mark.parametrize("initial", ["queued", "processing", "failed", "needs_ocr"])
def test_delete_nonready_cancels_ingest_and_never_claims_it(worker_env, initial):
    env = worker_env
    uploaded = env.upload()
    attempt = env.queue.claim() if initial == "processing" else None
    with env.sessions() as db:
        db.get(Document, uploaded["document_id"]).status = initial
        db.commit()
    remove(env, uploaded["document_id"])
    assert env.queue.claim() is None
    if attempt:
        with pytest.raises(LeaseLost):
            env.queue.touch(attempt)
    assert cleanup(env).run_once()["status"] == "completed"
    assert doc_state(env, uploaded["document_id"]).status == "deleted"


def test_scope_role_and_concurrent_delete_are_enforced(chat_env):
    env = chat_env
    doc_id = ready(env)["document_id"]
    assert env.client.delete(f"/api/v1/documents/{doc_id}").status_code == 401
    with env.sessions() as db:
        db.get(User, env.user.id).role = "member"
        db.commit()
    assert env.client.delete(f"/api/v1/documents/{doc_id}", headers=env.auth).status_code == 403
    with env.sessions() as db:
        db.get(User, env.user.id).role = "knowledge_admin"
        db.commit()
    assert (
        env.client.delete(f"/api/v1/documents/{uuid.uuid4()}", headers=env.auth).status_code == 404
    )
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: remove(env, doc_id), range(2)))
    assert results[0][0]["job_id"] == results[1][0]["job_id"]
    assert doc_state(env, doc_id).lifecycle_version == 2


def test_cleanup_failure_stays_hidden_exhausts_and_concurrent_admin_retry(worker_env, monkeypatch):
    env = worker_env
    uploaded = env.upload()
    result, _ = remove(env, uploaded["document_id"])
    original = env.vector.delete_document

    def unavailable(*args):
        raise WorkerError("vector_unavailable", True)

    monkeypatch.setattr(env.vector, "delete_document", unavailable)
    worker = cleanup(env)
    for _ in range(env.settings.job_max_attempts):
        assert worker.run_once()["error_code"] == "vector_unavailable"
        assert doc_state(env, uploaded["document_id"]).status == "deleting"
        make_due(env, result["job_id"])
    with env.sessions() as db:
        job = db.get(ProcessingJob, result["job_id"])
        assert job.status == "failed" and job.retryable and job.attempts == 3

    def retry(_):
        with env.sessions() as db:
            return retry_cleanup(db, result["job_id"], env.user)

    with ThreadPoolExecutor(2) as pool:
        retried = list(pool.map(retry, range(2)))
    assert retried[0]["job_id"] == retried[1]["job_id"]
    monkeypatch.setattr(env.vector, "delete_document", original)
    assert worker.run_once()["status"] == "completed"


def test_expired_cleanup_is_recovered_and_old_attempt_cannot_finish(worker_env):
    env = worker_env
    value, _ = remove(env, env.upload()["document_id"])
    queue = CleanupQueue(env.sessions, env.settings)
    attempt = queue.claim()
    make_due(env, value["job_id"], expired=True)
    assert queue.recover_expired() == 1
    make_due(env, value["job_id"])
    with pytest.raises(LeaseLost):
        queue.finish(attempt)
    assert CleanupWorker(queue, env.vector).run_once()["status"] == "completed"


@pytest.mark.parametrize("lost_ack", [False, True])
def test_cleanup_db_failure_after_external_deletes_is_idempotent(worker_env, monkeypatch, lost_ack):
    env = worker_env
    uploaded = env.upload()
    remove(env, uploaded["document_id"])
    original = Session.commit
    fired = []

    def commit(db):
        finishing = any(isinstance(row, Document) and row.status == "deleted" for row in db.dirty)
        if finishing and not fired:
            fired.append(True)
            if lost_ack:
                original(db)
            raise OperationalError("test-only", {}, Exception("private SQL details"))
        return original(db)

    monkeypatch.setattr(Session, "commit", commit)
    worker = cleanup(env)
    result = worker.run_once()
    assert fired
    if lost_ack:
        assert result["status"] == "completed" and result["recovered_commit_ack"]
    else:
        assert result["error_code"] == "database_unavailable"
        with env.sessions() as db:
            job_id = db.scalar(
                select(ProcessingJob.id).where(
                    ProcessingJob.kind == "cleanup",
                    ProcessingJob.document_id == uploaded["document_id"],
                )
            )
        make_due(env, job_id)
        assert worker.run_once()["status"] == "completed"
    assert doc_state(env, uploaded["document_id"]).status == "deleted"


def test_late_upsert_after_delete_is_not_published_and_is_reconciled(worker_env, monkeypatch):
    env = worker_env
    doc_id = env.upload()["document_id"]
    entered, release = threading.Event(), threading.Event()
    original = env.vector.upsert

    def blocked(points):
        entered.set()
        assert release.wait(20)
        return original(points)

    monkeypatch.setattr(env.vector, "upsert", blocked)
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(env.worker().run_once)
        try:
            assert entered.wait(15)
            remove(env, doc_id)
            assert cleanup(env).run_once()["status"] == "completed"
        finally:
            release.set()
        assert future.result(timeout=15)["status"] == "lease_lost"
    assert doc_state(env, doc_id).status == "deleted"
    assert env.vector.document_points(env.user.workspace_id, doc_id)
    assert cleanup(env).reconcile_deleted() == 1
    assert not env.vector.document_points(env.user.workspace_id, doc_id)


def test_delete_during_generation_fails_without_resurrecting_trace_or_answer(chat_env):
    env = chat_env
    doc_id = ready(env, b"S9 query-race private source.")["document_id"]
    entered, release = threading.Event(), threading.Event()
    env.provider.callback = lambda: (entered.set(), release.wait(20))
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(env.ask)
        try:
            assert entered.wait(15)
            remove(env, doc_id)
            assert cleanup(env).run_once()["status"] == "completed"
        finally:
            release.set()
        response = future.result(timeout=15)
    assert response.status_code == 409, response.text
    with env.sessions() as db:
        run = db.scalar(
            select(QueryRun).where(QueryRun.session_id == uuid.UUID(env.payload["session_id"]))
        )
        assert run.status == "failed" and run.error_code == "source_changed"
        assert "S9 query-race" not in json.dumps(run.retrieval_trace_json)
        assert list(
            db.scalars(select(ChatMessage.role).where(ChatMessage.query_run_id == run.id))
        ) == ["user"]


def test_delete_during_counting_prevents_any_generation_and_registration(chat_env):
    env = chat_env
    doc_id = ready(env)["document_id"]
    entered, release = threading.Event(), threading.Event()
    original = env.provider.count_tokens

    def blocked(payload, deadline):
        if not entered.is_set():
            entered.set()
            assert release.wait(20)
        return original(payload, deadline)

    env.provider.count_tokens = blocked
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(env.ask)
        try:
            assert entered.wait(15)
            remove(env, doc_id)
            assert cleanup(env).run_once()["status"] == "completed"
        finally:
            release.set()
        assert future.result(timeout=15).status_code == 409
    assert not env.provider.calls
    assert len(env.provider.counts) == 1  # no evidence text sent by subsequent count calls
    with env.sessions() as db:
        run = db.scalar(
            select(QueryRun).where(QueryRun.session_id == uuid.UUID(env.payload["session_id"]))
        )
        assert not run.retrieval_trace_json.get("evidence_map")


def test_legacy_full_context_and_uncited_source_copies_are_redacted(chat_env):
    env = chat_env
    ready(env, b"S9 first private source.")
    ready(env, b"S9 second unaffected document.")
    result = env.ask().json()["data"]
    # Inject an old Step08/debug trace to prove legacy text is purged, too.
    with env.sessions() as db:
        run = db.get(QueryRun, uuid.UUID(result["run_id"]))
        trace = json.loads(json.dumps(run.retrieval_trace_json))
        cited = {citation["document_id"] for citation in result["citations"]}
        uncited_id = uuid.UUID(
            next(
                row["document_id"]
                for row in trace["evidence_map"]
                if row["document_id"] not in cited
            )
        )
        trace["evidence_map"][0]["excerpt"] = "S9 legacy private excerpt"
        trace["evidence_map"][0]["source_spans"][0]["raw_text"] = "S9 nested debug copy"
        trace["debug"] = {"raw_prompt": "S9 full context copy"}
        run.retrieval_trace_json = dict(trace)
        db.commit()
    remove(env, uncited_id)
    with env.sessions() as db:
        run = db.get(QueryRun, uuid.UUID(result["run_id"]))
        assert "S9" not in json.dumps(run.retrieval_trace_json)
        assert db.get(ChatMessage, uuid.UUID(result["message_id"])).structured_answer_json is None
    assert env.ask().json()["data"]["source_unavailable"]


def test_unsafe_storage_path_fails_closed_without_touching_outside_file(worker_env, tmp_path):
    env = worker_env
    uploaded = env.upload()
    sentinel = tmp_path / "must-remain.txt"
    sentinel.write_text("outside sentinel", encoding="utf-8")
    with env.sessions() as db:
        revision = db.scalar(
            select(DocumentRevision).where(DocumentRevision.document_id == uploaded["document_id"])
        )
        revision.storage_key = "../must-remain.txt"
        db.commit()
    remove(env, uploaded["document_id"])
    result = cleanup(env).run_once()
    assert result["error_code"] == "storage_key_invalid" and not result["retryable"]
    assert sentinel.read_text() == "outside sentinel"
    assert doc_state(env, uploaded["document_id"]).status == "deleting"


def test_foreign_workspace_delete_and_cleanup_retry_return_404(chat_env):
    env = chat_env
    other_workspace, other_user, other_doc, other_job = [uuid.uuid4() for _ in range(4)]
    with env.sessions() as db:
        db.add(Workspace(id=other_workspace, name="S9 foreign scope fixture"))
        db.flush()
        db.add(
            User(
                id=other_user,
                workspace_id=other_workspace,
                username="s9." + other_user.hex,
                email=other_user.hex + "@example.invalid",
                display_name="other",
                role="knowledge_admin",
                password_hash="unused",
            )
        )
        db.flush()
        db.add(
            Document(
                id=other_doc,
                workspace_id=other_workspace,
                created_by=other_user,
                filename="foreign-private.txt",
                mime="text/plain",
                size_bytes=0,
                sha256="a" * 64,
                status="deleting",
            )
        )
        db.flush()
        db.add(
            ProcessingJob(
                id=other_job,
                document_id=other_doc,
                entity_type="document",
                entity_id=other_doc,
                kind="cleanup",
                stage="cleanup",
            )
        )
        db.commit()
    try:
        for method, path in [
            ("DELETE", f"/api/v1/documents/{other_doc}"),
            ("POST", f"/api/v1/jobs/{other_job}/retry"),
        ]:
            response = env.client.request(method, path, headers=env.auth)
            assert response.status_code == 404 and "foreign-private" not in response.text
    finally:
        with env.sessions() as db:
            db.execute(delete(ProcessingJob).where(ProcessingJob.id == other_job))
            db.execute(delete(Document).where(Document.id == other_doc))
            db.execute(delete(User).where(User.id == other_user))
            db.execute(delete(Workspace).where(Workspace.id == other_workspace))
            db.commit()


def test_multiple_collections_scoped_vector_filter_and_missing_files(worker_env):
    env = worker_env
    first, second = env.upload(b"First scoped source."), env.upload(b"Second source stays.")
    assert env.worker().run_once()["status"] == "completed"
    assert env.worker().run_once()["status"] == "completed"
    second_collection = QdrantIndex(env.settings.qdrant_url, "s6_test_" + uuid.uuid4().hex[:12], 2)
    second_collection.ensure_collection(env.profile["embedding_hash"])
    wrong_workspace = uuid.uuid4()
    try:
        point = dict(env.vector.document_points(env.user.workspace_id, first["document_id"])[0])
        point["vector"] = [1.0] + [0.0] * 383
        second_collection.upsert([point])
        wrong = {
            **point,
            "id": str(uuid.uuid4()),
            "payload": {**point["payload"], "workspace_id": str(wrong_workspace)},
        }
        env.vector.upsert([wrong])
        with env.sessions() as db:
            rev = db.scalar(
                select(DocumentRevision).where(DocumentRevision.document_id == first["document_id"])
            )
            (env.settings.storage_dir / rev.storage_key).unlink()
            db.add(
                DocumentRevision(
                    document_id=first["document_id"],
                    version=2,
                    status="retired",
                    storage_key="",
                    collection_name=second_collection.collection,
                )
            )
            db.commit()
        remove(env, first["document_id"])
        assert cleanup(env).run_once()["status"] == "completed"
        assert not second_collection.document_points(env.user.workspace_id, first["document_id"])
        assert not env.vector.document_points(env.user.workspace_id, first["document_id"])
        assert env.vector.document_points(wrong_workspace, first["document_id"])
        assert env.vector.document_points(env.user.workspace_id, second["document_id"])
    finally:
        second_collection._request("DELETE", allow_missing=True)
        second_collection.close()


def test_missing_collection_is_success_without_recreation(worker_env):
    env = worker_env
    remove(env, env.upload()["document_id"])
    env.vector._request("DELETE")
    assert cleanup(env).run_once()["status"] == "completed"
    assert env.vector._request("GET", allow_missing=True) is None


def test_file_failure_is_retried_and_logs_keep_no_source_text(worker_env, monkeypatch, caplog):
    env = worker_env
    uploaded = env.upload(b"PRIVATE-S9-FILE-CONTENT")
    result, _ = remove(env, uploaded["document_id"])
    worker = cleanup(env)
    original = worker._remove_file
    caplog.set_level(logging.INFO)

    def denied(*args):
        raise WorkerError("file_cleanup_failed", True)

    monkeypatch.setattr(worker, "_remove_file", denied)
    assert worker.run_once()["error_code"] == "file_cleanup_failed"
    assert "cleanup job_id=" in caplog.text
    assert "PRIVATE-S9-FILE-CONTENT" not in caplog.text
    make_due(env, result["job_id"])
    monkeypatch.setattr(worker, "_remove_file", original)
    assert worker.run_once()["status"] == "completed"


def test_cleanup_only_cli_has_no_model_cache_dependency(worker_env):
    env = worker_env
    doc_id = env.upload()["document_id"]
    remove(env, doc_id)
    process_env = dict(
        os.environ,
        DATABASE_URL=env.settings.test_database_url,
        HF_HOME=str(env.settings.storage_dir / "no-model-cache"),
        FILE_STORAGE_DIR=str(env.settings.storage_dir),
        QDRANT_COLLECTION=env.vector.collection,
    )
    result = subprocess.run(
        [sys.executable, "-B", "-m", "app.worker", "--cleanup-only", "--once"],
        env=process_env,
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert result.returncode == 0, result.stderr
    assert doc_state(env, doc_id).status == "deleted"


@pytest.mark.parametrize("lost_ack", [False, True])
def test_delete_commit_failure_or_lost_ack_never_returns_false_success(
    chat_env, monkeypatch, lost_ack
):
    env = chat_env
    doc_id = ready(env)["document_id"]
    original = Session.commit
    fired = []

    def commit(db):
        # delete_document flushes before commit; flushed objects are no longer dirty.
        deleting = any(
            isinstance(row, Document) and row.status == "deleting"
            for row in db.identity_map.values()
        )
        if deleting and not fired:
            fired.append(True)
            if lost_ack:
                original(db)
            raise OperationalError("test-only", {}, Exception("private source SQL"))
        return original(db)

    monkeypatch.setattr(Session, "commit", commit)
    result = env.client.delete(f"/api/v1/documents/{doc_id}", headers=env.auth)
    assert result.status_code == 503 and "private source SQL" not in result.text
    assert fired
    if lost_ack:
        retry = env.client.delete(f"/api/v1/documents/{doc_id}", headers=env.auth)
        assert retry.status_code == 202
        with env.sessions() as db:
            assert (
                len(
                    db.scalars(
                        select(ProcessingJob).where(
                            ProcessingJob.document_id == doc_id, ProcessingJob.kind == "cleanup"
                        )
                    ).all()
                )
                == 1
            )
    else:
        assert doc_state(env, doc_id).status == "ready"
        assert env.vector.document_points(env.user.workspace_id, doc_id)


def test_admin_cleanup_retry_route_and_member_denial(chat_env, monkeypatch):
    env = chat_env
    doc_id = ready(env)["document_id"]
    result = env.client.delete(f"/api/v1/documents/{doc_id}", headers=env.auth).json()["data"]
    worker = cleanup(env)
    worker.queue.settings.job_max_attempts = 1
    original = env.vector.delete_document
    monkeypatch.setattr(
        env.vector,
        "delete_document",
        lambda *args: (_ for _ in ()).throw(WorkerError("vector_unavailable", True)),
    )
    assert worker.run_once()["status"] == "error"
    path = f"/api/v1/jobs/{result['job_id']}/retry"
    with env.sessions() as db:
        db.get(User, env.user.id).role = "member"
        db.commit()
    assert env.client.post(path, headers=env.auth).status_code == 403
    with env.sessions() as db:
        db.get(User, env.user.id).role = "knowledge_admin"
        db.commit()
    retry = env.client.post(path, headers=env.auth)
    assert retry.status_code == 202, retry.text
    assert (
        env.client.post(path, headers=env.auth).json()["data"]["job_id"]
        == retry.json()["data"]["job_id"]
    )
    monkeypatch.setattr(env.vector, "delete_document", original)
    assert worker.run_once()["status"] == "completed"
    assert env.client.post(path, headers=env.auth).status_code == 409


def test_production_search_keeps_only_unrelated_active_source_before_cleanup(chat_env):
    env = chat_env
    deleted_id = ready(env, b"PRIVATE-DELETED-S9")["document_id"]
    kept_id = ready(env, b"KEPT-S9-SOURCE")["document_id"]

    class QueryEncoder:
        def encode_query(self, text):
            return [1.0] + [0.0] * 383

    env.app.state.search_runtime = SimpleNamespace(
        profile=env.profile,
        vector=env.vector,
        embedder=QueryEncoder(),
        counter=SimpleNamespace(count_query=lambda text: 10),
        lock=threading.Lock(),
        close=lambda: None,
    )
    remove(env, deleted_id)
    # Intentionally leave the old vectors present to prove SQL eligibility is decisive.
    assert env.vector.document_points(env.user.workspace_id, deleted_id)
    response = env.client.post("/api/v1/search", headers=env.auth, json={"query": "policy"})
    assert response.status_code == 200, response.text
    assert {hit["document_id"] for hit in response.json()["data"]["hits"]} == {str(kept_id)}
    assert "PRIVATE-DELETED-S9" not in response.text
    filtered = env.client.post(
        "/api/v1/search",
        headers=env.auth,
        json={"query": "policy", "filters": {"document_ids": [str(deleted_id)]}},
    )
    assert filtered.status_code == 410


def test_normal_worker_does_not_starve_cleanup_when_sweeper_fails(worker_env, monkeypatch):
    from app import worker as module

    env = worker_env
    doc_id = env.upload()["document_id"]
    remove(env, doc_id)
    monkeypatch.setattr(sys, "argv", ["worker", "--once"])
    monkeypatch.setattr(module.signal, "signal", lambda *args: None)
    monkeypatch.setattr(module, "get_settings", lambda: env.settings)
    monkeypatch.setattr(module, "get_sessionmaker", lambda: env.sessions)
    monkeypatch.setattr(module, "frozen_profile", lambda settings: env.profile)
    monkeypatch.setattr(module, "E5TokenCounter", lambda *args: env.counter)
    monkeypatch.setattr(
        module,
        "LocalEmbedder",
        lambda *args: SimpleNamespace(encode=env.embedder.encode, close=lambda: None),
    )

    def sweep():
        raise WorkerError("vector_unavailable", True)

    monkeypatch.setattr(module, "OrphanCleaner", lambda *args: SimpleNamespace(sweep=sweep))
    assert module.main() == 1  # maintenance failure remains visible
    assert doc_state(env, doc_id).status == "deleted"  # durable job ran before that failure


def test_delete_after_invalid_first_output_prevents_repair_resending_context(chat_env):
    from tests.test_answering import FakeProvider, output

    env = chat_env
    doc_id = ready(env)["document_id"]
    env.provider = FakeProvider([output(ids=["E99"])], callback=lambda: remove(env, doc_id))
    response = env.ask()
    assert response.status_code == 409, response.text
    assert len(env.provider.calls) == 1
