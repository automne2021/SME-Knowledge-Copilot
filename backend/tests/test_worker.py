"""Real PostgreSQL/Qdrant reliability contracts. Embeddings here are labeled test fakes."""

import multiprocessing
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.models import (
    Chunk,
    Document,
    DocumentRevision,
    ProcessingJob,
    SourceBlock,
)
from app.services.chunking import split_document
from app.services.embeddings import LocalEmbedder, validate_vectors
from app.services.jobs import JobQueue
from app.services.orphans import OrphanCleaner
from app.services.parsing import parse_file
from app.services.vectors import QdrantIndex
from app.services.worker_errors import LeaseLost, WorkerError
from app.worker import IngestionWorker
from tests.test_parsing_chunking import MANIFEST, SNAPSHOT, CharacterCounter
from tests.worker_support import FakeEmbedder


def state(env, document_id):
    with env.sessions() as db:
        document = db.get(Document, document_id)
        job = db.scalar(select(ProcessingJob).where(ProcessingJob.document_id == document_id))
        revision = db.get(DocumentRevision, job.revision_id)
        return document, job, revision


def due_now(env, job_id, expire=False):
    with env.sessions() as db:
        job = db.get(ProcessingJob, job_id)
        if expire:
            job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
        else:
            job.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()


def test_complete_generation_has_exact_sql_vector_and_source_mapping(worker_env):
    env = worker_env
    uploaded = env.upload()
    result = env.worker().run_once()
    document, job, revision = state(env, uploaded["document_id"])
    assert result["status"] == "completed" and env.worker().run_once() is None
    assert document.status == revision.status == "ready" and job.status == "completed"
    assert document.active_generation_id == job.generation_id
    assert revision.expected_chunk_count == result["chunk_count"]
    points = list(env.vector.scroll(job.generation_id))
    assert (
        sorted(str(point["id"]) for point in points)
        == job.attempt_manifest_json["identity"]["point_ids"]
    )
    assert all("text" not in point["payload"] for point in points)
    with env.sessions() as db:
        for chunk in db.scalars(select(Chunk).where(Chunk.generation_id == job.generation_id)):
            parts = []
            for span in chunk.source_spans_json:
                block = db.get(SourceBlock, uuid.UUID(span["block_id"]))
                parts.append(block.normalized_text[span["char_start"] : span["char_end"]])
            assert "\n".join(parts) == chunk.text


def test_concurrent_claim_and_skip_locked(worker_env):
    env = worker_env
    uploaded = env.upload()
    with env.sessions() as db:
        db.scalar(select(Document).where(Document.id == uploaded["document_id"]).with_for_update())
        with ThreadPoolExecutor(1) as pool:
            # A new libpq connection may try localhost IPv6 before IPv4 on Windows.
            assert pool.submit(env.queue.claim).result(timeout=15) is None
    with ThreadPoolExecutor(2) as pool:
        claims = list(pool.map(lambda _: env.queue.claim(), range(2)))
    assert sum(attempt is not None for attempt in claims) == 1


def test_heartbeat_runs_during_inference_without_document_lock(worker_env):
    env = worker_env
    uploaded = env.upload()
    entered, release = threading.Event(), threading.Event()

    class SlowEmbedder(FakeEmbedder):
        def encode(self, texts):
            entered.set()
            assert release.wait(8)
            return super().encode(texts)

    env.embedder = SlowEmbedder()
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(env.worker().run_once)
        try:
            assert entered.wait(8)
            time.sleep(2.2)  # longer than the original 2-second lease
            with env.sessions() as db:
                document = db.scalar(
                    select(Document)
                    .where(Document.id == uploaded["document_id"])
                    .with_for_update(nowait=True)
                )
                job = db.scalar(
                    select(ProcessingJob).where(ProcessingJob.document_id == document.id)
                )
                assert job.lease_expires_at > datetime.now(UTC)
        finally:
            release.set()
        assert future.result(timeout=8)["status"] == "completed"


def test_old_attempt_is_fenced_after_recovery(worker_env):
    env = worker_env
    uploaded = env.upload()
    old = env.queue.claim()
    parsed = parse_file(env.settings.storage_dir / old.storage_key, "txt")
    chunks = split_document(parsed, env.counter)
    _, identity = env.queue.persist(old, parsed, chunks, env.profile)
    due_now(env, old.job_id, expire=True)
    assert env.queue.recover_expired() == 1
    due_now(env, old.job_id)
    new = env.queue.claim()
    assert old.generation_id != new.generation_id and old.lease_token != new.lease_token
    for action in [
        lambda: env.queue.touch(old),
        lambda: env.queue.publish(old, identity, {}),
        lambda: env.queue.persist(old, parsed, chunks, env.profile),
        lambda: env.queue.fail(old, WorkerError("old", True)),
    ]:
        with pytest.raises(LeaseLost):
            action()
    assert state(env, uploaded["document_id"])[0].active_generation_id is None


def test_publish_rollback_never_marks_staging_ready_then_retries(worker_env):
    env = worker_env
    uploaded = env.upload()
    failed = []

    def fail_publish(session):
        if not failed and any(
            isinstance(row, Document) and row.status == "ready" for row in session.dirty
        ):
            failed.append(True)
            raise OperationalError("injected publish failure", None, Exception())

    event.listen(Session, "before_commit", fail_publish)
    try:
        result = env.worker().run_once()
    finally:
        event.remove(Session, "before_commit", fail_publish)
    assert result["error_code"] == "database_unavailable"
    document, job, revision = state(env, uploaded["document_id"])
    old_generation = job.generation_id
    assert job.status == "retry_wait" and document.active_generation_id is None
    assert revision.status == "staging" and list(env.vector.scroll(old_generation))
    due_now(env, job.id)
    assert env.worker().run_once()["status"] == "completed"
    document, job, _ = state(env, document.id)
    assert document.active_generation_id != old_generation and job.attempts == 2


def test_lost_publish_ack_does_not_fail_completed_job(worker_env):
    env = worker_env
    uploaded = env.upload()
    failed = []

    def mark_publish(session):
        if any(isinstance(row, Document) and row.status == "ready" for row in session.dirty):
            session.info["test_publish"] = True

    def lost_ack(session):
        if session.info.get("test_publish") and not failed:
            failed.append(True)
            raise OperationalError("injected lost ack", None, Exception())

    event.listen(Session, "before_commit", mark_publish)
    event.listen(Session, "after_commit", lost_ack)
    try:
        result = env.worker().run_once()
    finally:
        event.remove(Session, "before_commit", mark_publish)
        event.remove(Session, "after_commit", lost_ack)
    assert result["status"] == "completed" and result["recovered_commit_ack"] is True
    assert state(env, uploaded["document_id"])[1].status == "completed"


@pytest.mark.parametrize(
    "code,retryable",
    [("vector_unavailable", True), ("embedding_timeout", True), ("invalid_embedding", False)],
)
def test_typed_failure_retry_budget(worker_env, code, retryable):
    env = worker_env
    uploaded = env.upload()

    class FailingEmbedder:
        def encode(self, texts):
            raise WorkerError(code, retryable)

    env.embedder = FailingEmbedder()
    for index in range(3 if retryable else 1):
        assert env.worker().run_once()["error_code"] == code
        document, job, revision = state(env, uploaded["document_id"])
        assert job.attempts == index + 1 and document.active_generation_id is None
        if retryable and index < 2:
            assert job.status == "retry_wait" and revision.status == "staging"
            assert job.next_retry_at > datetime.now(UTC)
            due_now(env, job.id)
    assert job.status == "failed" and document.status == revision.status == "failed"
    assert job.retryable == retryable and env.worker().run_once() is None


def _pause_after_upsert(url, settings_values, profile, marker):
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    settings = Settings(_env_file=None, **settings_values)

    class PausedIndex(QdrantIndex):
        def upsert(self, points):
            super().upsert(points)
            marker.set()
            time.sleep(30)

    vector = PausedIndex(settings.qdrant_url, settings.qdrant_collection, 2)
    queue = JobQueue(sessionmaker(engine, expire_on_commit=False), settings)
    IngestionWorker(queue, vector, FakeEmbedder(), CharacterCounter(), profile).run_once()


def test_kill_restart_after_partial_upsert_then_orphan_cleanup(worker_env, db_engine):
    env = worker_env
    uploaded = env.upload(b"A policy condition applies before approval. " * 60)
    settings_values = {
        name: getattr(env.settings, name)
        for name in (
            "database_url",
            "storage_dir",
            "qdrant_url",
            "qdrant_collection",
            "job_lease_seconds",
            "job_heartbeat_seconds",
            "embedding_timeout_seconds",
            "orphan_grace_seconds",
            "vector_timeout_seconds",
        )
    }
    settings_values["database_url"] = db_engine.url.render_as_string(hide_password=False)
    context = multiprocessing.get_context("spawn")
    marker = context.Event()
    process = context.Process(
        target=_pause_after_upsert,
        args=(settings_values["database_url"], settings_values, env.profile, marker),
    )
    process.start()
    try:
        assert marker.wait(15), "child worker did not reach its first real Qdrant upsert"
        process.terminate()
        process.join(8)
        assert not process.is_alive()
        document, job, _ = state(env, uploaded["document_id"])
        old = job.generation_id
        assert document.active_generation_id is None and document.status == "processing"
        assert len(list(env.vector.scroll(old))) == 4
        due_now(env, job.id, expire=True)
        assert env.queue.recover_expired() == 1
        due_now(env, job.id)
        assert env.worker().run_once()["status"] == "completed"
        document, job, _ = state(env, document.id)
        assert document.active_generation_id != old and job.attempts == 2
        env.vector._request(
            "POST",
            "/points/payload",
            params={"wait": "true"},
            json={
                "payload": {"attempt_started_epoch": 0},
                "filter": env.vector.generation_filter(old),
            },
        )
        with env.sessions() as db:
            for model in (Chunk, SourceBlock):
                db.execute(
                    update(model)
                    .where(model.generation_id == old)
                    .values(created_at=datetime.now(UTC) - timedelta(hours=1))
                )
            db.commit()
        assert OrphanCleaner(env.sessions, env.settings, env.vector).sweep()["generations"] == 1
        assert not list(env.vector.scroll(old))
        assert len(list(env.vector.scroll(document.active_generation_id))) > 4
        with env.sessions() as db:
            assert db.scalar(select(Chunk.id).where(Chunk.generation_id == old)) is None
        # Late stale writes are removed by the next reconciliation as well.
        point = {
            "id": str(uuid.uuid4()),
            "vector": [1.0] + [0.0] * 383,
            "payload": {"generation_id": str(old), "attempt_started_epoch": 0},
        }
        env.vector.upsert([point])
        assert OrphanCleaner(env.sessions, env.settings, env.vector).sweep()["generations"] == 1
    finally:
        if process.is_alive():
            process.terminate()
            process.join(8)
        process.close()


def test_orphan_files_only_old_canonical_unreferenced_are_removed(worker_env):
    env = worker_env
    uploaded = env.upload()
    _, _, revision = state(env, uploaded["document_id"])
    referenced = env.settings.storage_dir / revision.storage_key
    old = env.settings.storage_dir / uuid.uuid4().hex / (uuid.uuid4().hex + ".txt")
    old.parent.mkdir()
    old.write_bytes(b"orphan")
    fresh = old.with_name(uuid.uuid4().hex + ".txt")
    fresh.write_bytes(b"inflight")
    unrelated = old.with_name("user-file.txt")
    unrelated.write_bytes(b"keep")
    for path in (old, referenced, unrelated):
        os.utime(path, (0, 0))
    result = OrphanCleaner(env.sessions, env.settings, env.vector).sweep()
    assert result["files"] == 1 and not old.exists()
    assert referenced.exists() and fresh.exists() and unrelated.exists()


@pytest.mark.parametrize(
    "vector", [[1.0] * 383, [float("nan")] * 384, [0.0] * 384, [True] + [0.0] * 383]
)
def test_invalid_vectors_rejected_before_index(vector):
    with pytest.raises(WorkerError, match="invalid_embedding"):
        validate_vectors([vector], 1)


def test_model_subprocess_startup_has_hard_deadline():
    settings = get_settings().model_copy(update={"embedding_timeout_seconds": 0.001})
    embedder = LocalEmbedder({"snapshot": "missing-test-snapshot"}, settings)
    with pytest.raises(WorkerError, match="embedding_timeout"):
        embedder.encode(["A test input"])
    assert embedder.process is None and embedder.connection is None


def _stall_model_batch(connection, snapshot, threads):
    connection.send({"ready": True})
    connection.recv()
    time.sleep(30)


def test_model_batch_timeout_terminates_started_child(monkeypatch):
    from app.services import embeddings

    monkeypatch.setattr(embeddings, "_model_process", _stall_model_batch)
    settings = get_settings().model_copy(update={"embedding_timeout_seconds": 5})
    embedder = LocalEmbedder({"snapshot": "test-only-no-model"}, settings)
    with pytest.raises(WorkerError, match="embedding_timeout"):
        embedder.encode(["A test input"])
    assert embedder.load_seconds > 0  # startup completed; the batch itself exceeded its deadline
    assert embedder.process is None and embedder.connection is None


@pytest.mark.parametrize(
    "name,status,code",
    [
        ("scan.pdf", "needs_ocr", "needs_ocr"),
        ("blank.pdf", "failed", "no_extractable_text"),
        ("encrypted.pdf", "failed", "encrypted_document"),
        ("malformed.pdf", "failed", "parse_failed"),
        ("mixed.pdf", "ready", None),
    ],
)
def test_parser_errors_are_real_terminal_job_states(worker_env, name, status, code):
    env = worker_env
    entry = next(item for item in MANIFEST["fixtures"] if item["path"].endswith("/" + name))
    uploaded = env.upload((SNAPSHOT / entry["path"]).read_bytes(), "pdf")
    env.worker().run_once()
    document, job, revision = state(env, uploaded["document_id"])
    assert document.status == status and job.error_code == code and job.attempts == 1
    assert job.status == ("completed" if status == "ready" else "failed")
    assert job.retryable is False
    if status != "ready":
        assert document.active_generation_id is None and revision.status == "failed"
    else:
        assert document.warnings_json == [{"code": "partial_text_extraction", "skipped_pages": [2]}]


def test_missing_vectors_prevent_publication(worker_env, monkeypatch):
    env = worker_env
    uploaded = env.upload()
    original = env.vector.upsert

    def disappear(points):
        original(points)
        env.vector.delete_generation(points[0]["payload"]["generation_id"])

    monkeypatch.setattr(env.vector, "upsert", disappear)
    assert env.worker().run_once()["error_code"] == "vector_manifest_mismatch"
    document, job, _ = state(env, uploaded["document_id"])
    assert document.status == job.status == "failed" and document.active_generation_id is None


def test_sql_manifest_tamper_and_delete_fence(worker_env):
    env = worker_env
    uploaded = env.upload()
    attempt = env.queue.claim()
    parsed = parse_file(env.settings.storage_dir / attempt.storage_key, "txt")
    _, identity = env.queue.persist(
        attempt, parsed, split_document(parsed, env.counter), env.profile
    )
    with env.sessions() as db:
        db.get(ProcessingJob, attempt.job_id).attempt_manifest_json = {
            "identity": {},
            "sha256": "bad",
        }
        db.commit()
    with pytest.raises(WorkerError, match="sql_manifest_mismatch"):
        env.queue.publish(attempt, identity, {})
    with env.sessions() as db:
        document = db.get(Document, uploaded["document_id"])
        document.status, document.lifecycle_version = "deleting", document.lifecycle_version + 1
        db.commit()
    with pytest.raises(LeaseLost):
        env.queue.publish(attempt, identity, {})
    due_now(env, attempt.job_id, expire=True)
    assert env.queue.recover_expired() == 1
    document, job, _ = state(env, uploaded["document_id"])
    assert document.status == "deleting" and job.status == "cancelled"


def test_sweeper_retains_old_active_generation_and_referenced_file(worker_env):
    env = worker_env
    uploaded = env.upload()
    assert env.worker().run_once()["status"] == "completed"
    document, _, revision = state(env, uploaded["document_id"])
    env.vector._request(
        "POST",
        "/points/payload",
        params={"wait": "true"},
        json={
            "payload": {"attempt_started_epoch": 0},
            "filter": env.vector.generation_filter(document.active_generation_id),
        },
    )
    with env.sessions() as db:
        for model in (Chunk, SourceBlock):
            db.execute(
                update(model)
                .where(model.generation_id == document.active_generation_id)
                .values(created_at=datetime.now(UTC) - timedelta(hours=1))
            )
        db.commit()
    path = env.settings.storage_dir / revision.storage_key
    os.utime(path, (0, 0))
    assert OrphanCleaner(env.sessions, env.settings, env.vector).sweep() == {
        "generations": 0,
        "files": 0,
    }
    assert path.exists() and list(env.vector.scroll(document.active_generation_id))


def test_fingerprint_mismatch_refuses_existing_collection(worker_env):
    with pytest.raises(WorkerError, match="vector_fingerprint_mismatch"):
        worker_env.vector.ensure_collection("different-embedding-fingerprint")


def test_shutdown_leaves_job_retryable(worker_env):
    env = worker_env
    uploaded = env.upload()
    worker = env.worker()
    worker.stop.set()
    assert worker.run_once()["error_code"] == "worker_shutdown"
    document, job, _ = state(env, uploaded["document_id"])
    assert job.status == "retry_wait" and document.active_generation_id is None
