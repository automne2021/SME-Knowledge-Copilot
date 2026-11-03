"""Upload authorization, stream limits, atomic metadata and real PostgreSQL dedup races."""

import asyncio
import hashlib
import io
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.core.config import get_settings
from app.core.errors import AppError
from app.models import Document, DocumentRevision, ProcessingJob, User, Workspace
from app.services.uploads import StoredUpload, register_upload, store_stream
from tests.test_rag_identity import headers


@pytest.fixture
def upload_root(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "storage_dir", tmp_path)
    return tmp_path


def send(client, person, name="policy.txt", body=b"Sample policy", mime="text/plain", **kwargs):
    return client.post(
        "/api/v1/documents",
        headers=headers(client, person),
        files={"file": (name, body, mime)},
        **kwargs,
    )


def test_upload_queues_one_atomic_revision_job(client, db_session, people, upload_root):
    response = send(client, people["admin"])
    assert response.status_code == 202
    data = response.json()["data"]
    assert data["status"] == "queued" and set(data) == {"document_id", "job_id", "status"}
    document = db_session.get(Document, uuid.UUID(data["document_id"]))
    revision = db_session.scalar(
        select(DocumentRevision).where(DocumentRevision.document_id == document.id)
    )
    job = db_session.get(ProcessingJob, uuid.UUID(data["job_id"]))
    assert document.workspace_id == people["admin"].workspace_id
    assert document.sha256 == hashlib.sha256(b"Sample policy").hexdigest()
    assert document.active_revision_id is None and revision.status == "staging"
    assert job.revision_id == revision.id and job.kind == "ingest" and job.stage == "validate"
    assert (upload_root / revision.storage_key).read_bytes() == b"Sample policy"
    assert "storage_key" not in response.text and "sha256" not in response.text


def test_member_and_anonymous_cannot_upload(client, people, upload_root):
    assert send(client, people["member"]).status_code == 403
    response = client.post("/api/v1/documents", files={"file": ("x.txt", b"x", "text/plain")})
    assert response.status_code == 401
    assert not list(upload_root.rglob("*.*"))


@pytest.mark.parametrize(
    "name,body,mime,status",
    [
        ("../escape.txt", b"policy", "text/plain", 422),
        ("C:\\outside.txt", b"policy", "text/plain", 422),
        ("fake.pdf", b"plain text", "application/pdf", 415),
        ("payload.txt", b"%PDF-1.7", "text/plain", 415),
        ("payload.exe", b"code", "application/octet-stream", 415),
        ("wrong.txt", b"text", "application/pdf", 415),
        ("empty.txt", b"", "text/plain", 202),  # parser assigns no_extractable_text in Step 06
    ],
)
def test_file_validation(client, people, upload_root, name, body, mime, status):
    response = send(client, people["admin"], name, body, mime)
    assert response.status_code == status
    if status != 202:
        assert not list(upload_root.rglob("*.*"))


def test_extra_fields_rejected_and_stream_size_bounded(client, people, upload_root, monkeypatch):
    assert (
        send(client, people["admin"], data={"workspace_id": str(uuid.uuid4())}).status_code == 422
    )
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    # Under request+framing cap, but over the actual file cap.
    response = send(client, people["admin"], body=b"x" * (1024**2 + 1))
    assert response.status_code == 413 and response.json()["error"]["code"] == "file_too_large"
    # Oversized total body; omit Content-Length to exercise streaming boundary as well.
    auth = headers(client, people["admin"])
    boundary = "bounded-upload"
    payload = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="large.txt"\r\nContent-Type: text/plain\r\n\r\n'
    ).encode()
    payload += b"a" * (1024**2 + 70_000) + f"\r\n--{boundary}--\r\n".encode()
    response = client.post(
        "/api/v1/documents",
        content=iter([payload[:50], payload[50:]]),
        headers=auth | {"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    assert response.status_code == 413 and response.json()["error"]["code"] == "file_too_large"
    assert not list(upload_root.rglob("*.*"))


def test_duplicate_renamed_and_cross_workspace(client, db_session, people, upload_root):
    first = send(client, people["admin"])
    second = send(client, people["admin"], name="renamed.md", mime="text/markdown")
    assert second.status_code == 409
    assert second.json()["error"]["details"]["document_id"] == first.json()["data"]["document_id"]
    people["other"].role = "knowledge_admin"
    db_session.flush()
    third = send(client, people["other"])
    assert third.status_code == 202
    assert third.json()["data"]["document_id"] != first.json()["data"]["document_id"]
    assert len(list(upload_root.rglob("*.*"))) == 2


def test_flush_failure_removes_source_and_metadata(db_session, people, upload_root, monkeypatch):
    path = upload_root / "source.txt"
    path.write_bytes(b"content")
    stored = StoredUpload(
        path, "source.txt", hashlib.sha256(b"content").hexdigest(), 7, uuid.uuid4(), uuid.uuid4()
    )
    original = db_session.flush

    def fail_on_job(*args, **kwargs):
        if any(isinstance(row, ProcessingJob) for row in db_session.new):
            raise RuntimeError("injected job failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(db_session, "flush", fail_on_job)
    with pytest.raises(RuntimeError, match="injected job failure"):
        register_upload(db_session, people["admin"], "source.txt", "txt", stored)
    assert not path.exists()
    assert db_session.get(Document, stored.document_id) is None
    assert db_session.get(DocumentRevision, stored.revision_id) is None


def test_commit_failure_removes_uncommitted_source(db_session, people, upload_root, monkeypatch):
    path = upload_root / "uncommitted.txt"
    path.write_bytes(b"content")
    stored = StoredUpload(
        path, path.name, hashlib.sha256(b"content").hexdigest(), 7, uuid.uuid4(), uuid.uuid4()
    )

    def fail_commit():
        raise RuntimeError("injected commit failure")

    monkeypatch.setattr(db_session, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="injected commit failure"):
        register_upload(db_session, people["admin"], "source.txt", "txt", stored)
    assert not path.exists()
    assert db_session.get(Document, stored.document_id) is None


def test_lost_commit_ack_preserves_committed_source(db_session, people, upload_root, monkeypatch):
    path = upload_root / "committed.txt"
    path.write_bytes(b"content")
    stored = StoredUpload(
        path, path.name, hashlib.sha256(b"content").hexdigest(), 7, uuid.uuid4(), uuid.uuid4()
    )
    commit = db_session.commit

    def lost_ack():
        commit()
        raise RuntimeError("lost commit acknowledgement")

    monkeypatch.setattr(db_session, "commit", lost_ack)
    with pytest.raises(RuntimeError, match="lost commit acknowledgement"):
        register_upload(db_session, people["admin"], "source.txt", "txt", stored)
    assert path.read_bytes() == b"content"
    assert db_session.get(Document, stored.document_id) is not None


def test_aborted_stream_does_not_leave_file(tmp_path):
    class AbortedUpload:
        async def read(self, size):
            raise OSError("injected interrupted stream")

    with pytest.raises(OSError, match="interrupted stream"):
        asyncio.run(store_stream(AbortedUpload(), tmp_path, uuid.uuid4(), "txt", 1024))
    assert not list(tmp_path.rglob("*.txt"))


def test_concurrent_duplicate_real_transactions(db_engine, tmp_path):
    workspace_id, user_id = uuid.uuid4(), uuid.uuid4()
    with Session(db_engine) as db, db.begin():
        db.add(Workspace(id=workspace_id, name="Isolated upload race"))
        db.flush()
        db.add(
            User(
                id=user_id,
                workspace_id=workspace_id,
                username="race." + user_id.hex,
                email=user_id.hex + "@example.invalid",
                display_name="Race test",
                password_hash="unused-service-test",
                role="knowledge_admin",
            )
        )
    barrier = threading.Barrier(2)

    def attempt(number):
        file = UploadFile(io.BytesIO(b"Identical bytes from two clients"))
        stored = asyncio.run(store_stream(file, tmp_path, workspace_id, "txt", 1024))
        barrier.wait(timeout=15)
        with Session(db_engine) as db:
            try:
                return 202, register_upload(
                    db,
                    SimpleNamespace(id=user_id, workspace_id=workspace_id),
                    f"name-{number}.txt",
                    "txt",
                    stored,
                )
            except AppError as exc:
                assert exc.code == "duplicate_document"
                return exc.status_code, exc.details

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
        assert sorted(status for status, _ in results) == [202, 409]
        assert len({str(result["document_id"]) for _, result in results}) == 1
        with Session(db_engine) as db:
            ids = select(Document.id).where(Document.workspace_id == workspace_id)
            for model, condition in [
                (Document, Document.workspace_id == workspace_id),
                (DocumentRevision, DocumentRevision.document_id.in_(ids)),
                (ProcessingJob, ProcessingJob.document_id.in_(ids)),
            ]:
                assert db.scalar(select(func.count()).select_from(model).where(condition)) == 1
        assert len(list(tmp_path.rglob("*.txt"))) == 1
    finally:
        with Session(db_engine) as db, db.begin():
            ids = select(Document.id).where(Document.workspace_id == workspace_id)
            db.execute(delete(ProcessingJob).where(ProcessingJob.document_id.in_(ids)))
            db.execute(delete(DocumentRevision).where(DocumentRevision.document_id.in_(ids)))
            db.execute(delete(Document).where(Document.workspace_id == workspace_id))
            db.execute(delete(User).where(User.id == user_id))
            db.execute(delete(Workspace).where(Workspace.id == workspace_id))


def test_retry_api_is_admin_scoped_and_idempotent(client, db_session, people, upload_root):
    uploaded = send(client, people["admin"]).json()["data"]
    document_id, original_job_id = uuid.UUID(uploaded["document_id"]), uuid.UUID(uploaded["job_id"])
    document = db_session.get(Document, document_id)
    job = db_session.get(ProcessingJob, original_job_id)
    document.status, job.status, job.retryable, job.error_code = (
        "failed",
        "failed",
        True,
        "vector_timeout",
    )
    db_session.get(DocumentRevision, job.revision_id).status = "failed"
    db_session.flush()
    path = f"/api/v1/documents/{document_id}/retry"
    assert client.post(path, headers=headers(client, people["member"])).status_code == 403
    people["other"].role = "knowledge_admin"
    db_session.flush()
    assert client.post(path, headers=headers(client, people["other"])).status_code == 404
    auth = headers(client, people["admin"])
    first = client.post(path, headers=auth)
    assert first.status_code == 202 and first.json()["data"]["status"] == "queued"
    assert first.json()["data"]["job_id"] != str(original_job_id)
    second = client.post(path, headers=auth)
    assert second.json()["data"]["job_id"] == first.json()["data"]["job_id"]
    metadata = client.get(f"/api/v1/documents/{document_id}", headers=auth).json()["data"]
    assert metadata["latest_job_id"] == first.json()["data"]["job_id"]
    assert db_session.get(ProcessingJob, original_job_id).status == "failed"


@pytest.mark.parametrize("status,retryable", [("needs_ocr", False), ("failed", False)])
def test_permanent_parser_error_cannot_manual_retry(
    client, db_session, people, upload_root, status, retryable
):
    uploaded = send(client, people["admin"]).json()["data"]
    document = db_session.get(Document, uuid.UUID(uploaded["document_id"]))
    job = db_session.get(ProcessingJob, uuid.UUID(uploaded["job_id"]))
    document.status, job.status, job.retryable = status, "failed", retryable
    db_session.flush()
    response = client.post(
        f"/api/v1/documents/{document.id}/retry", headers=headers(client, people["admin"])
    )
    assert response.status_code == 409 and response.json()["error"]["code"] == "retry_not_allowed"
