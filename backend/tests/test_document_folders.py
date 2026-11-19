"""Document classification, multipart boundaries and real PostgreSQL scope/locks."""

import hashlib
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models import Document, DocumentRevision, Folder, ProcessingJob, User, Workspace
from app.services.documents import move_document
from app.services.folders import delete_folder
from app.services.uploads import StoredUpload, register_upload
from tests.test_folders import folder
from tests.test_rag_identity import headers, make_document
from tests.test_uploads import send


@pytest.fixture
def storage(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "storage_dir", tmp_path)
    return tmp_path


@pytest.mark.parametrize("status", ["queued", "processing", "failed", "needs_ocr", "ready"])
def test_move_same_folder_and_unclassify_preserve_ingestion(client, db_session, people, status):
    first = folder(db_session, people["admin"])
    second = folder(db_session, people["admin"], "Kỹ thuật")
    doc = make_document(db_session, people["admin"])
    revision = DocumentRevision(document_id=doc.id, version=1, storage_key="test-only")
    db_session.add(revision)
    db_session.flush()
    doc.status = status
    if status == "ready":
        doc.active_revision_id, doc.active_generation_id = revision.id, uuid.uuid4()
    db_session.flush()
    before = (doc.active_revision_id, doc.active_generation_id, doc.lifecycle_version, doc.sha256)
    auth = headers(client, people["admin"])
    for target in [first.id, first.id, second.id, None]:
        response = client.patch(
            f"/api/v1/documents/{doc.id}",
            headers=auth,
            json={"folder_id": str(target) if target else None},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == str(doc.id)
        assert data["folder_id"] == (str(target) if target else None)
        assert data["status"] == status
        assert response.headers["Cache-Control"] == "no-store"
        assert "storage_key" not in data and "workspace_id" not in data
        detail = client.get(f"/api/v1/documents/{doc.id}", headers=auth)
        assert detail.json()["data"] == data
        db_session.refresh(doc)
        assert before == (
            doc.active_revision_id,
            doc.active_generation_id,
            doc.lifecycle_version,
            doc.sha256,
        )
        counts = client.get("/api/v1/folders", headers=auth).json()["data"]["items"]
        assert {r["id"]: r["ready_document_count"] for r in counts} == {
            str(first.id): int(status == "ready" and target == first.id),
            str(second.id): int(status == "ready" and target == second.id),
        }
    assert db_session.scalar(select(func.count()).select_from(ProcessingJob)) == 0
    assert db_session.scalar(select(func.count()).select_from(DocumentRevision)) == 1


@pytest.mark.parametrize("status", ["deleting", "deleted"])
def test_unavailable_document_cannot_be_reclassified(client, db_session, people, status):
    target = folder(db_session, people["admin"])
    doc = make_document(
        db_session,
        people["admin"],
        status=status,
        deleted_at=datetime.now(UTC) if status == "deleted" else None,
    )
    auth = headers(client, people["admin"])
    response = client.patch(
        f"/api/v1/documents/{doc.id}", headers=auth, json={"folder_id": str(target.id)}
    )
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "source_unavailable"
    db_session.refresh(doc)
    assert doc.folder_id is None


def test_patch_requires_admin_and_identity(client, db_session, people):
    doc = make_document(db_session, people["admin"])
    path = f"/api/v1/documents/{doc.id}"
    assert client.patch(path, json={"folder_id": None}).status_code == 401
    assert (
        client.patch(
            path, headers=headers(client, people["member"]), json={"folder_id": None}
        ).status_code
        == 403
    )


def test_patch_scope_rejects_foreign_missing_documents_and_folders(client, db_session, people):
    own = make_document(db_session, people["admin"])
    foreign = make_document(
        db_session, people["other"], status="deleted", deleted_at=datetime.now(UTC)
    )
    foreign_folder = folder(db_session, people["other"])
    auth = headers(client, people["admin"])
    for target in [foreign_folder.id, uuid.uuid4()]:
        response = client.patch(
            f"/api/v1/documents/{own.id}", headers=auth, json={"folder_id": str(target)}
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"
    for target in [foreign.id, uuid.uuid4()]:
        response = client.patch(
            f"/api/v1/documents/{target}", headers=auth, json={"folder_id": None}
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"
    db_session.refresh(own)
    assert own.folder_id is None


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"folder_id": ""},
        {"folder_id": "null"},
        {"folder_id": 42},
        {"folder_id": []},
        {"folder_id": None, "status": "ready"},
        {"folder_id": None, "workspace_id": str(uuid.uuid4())},
    ],
)
def test_patch_rejects_invalid_and_extra_fields(client, db_session, people, body):
    doc = make_document(db_session, people["admin"])
    assert (
        client.patch(
            f"/api/v1/documents/{doc.id}", headers=headers(client, people["admin"]), json=body
        ).status_code
        == 422
    )
    db_session.refresh(doc)
    assert doc.folder_id is None and doc.status == "queued"


def test_list_filters_before_limit_and_retains_current_status_rules(client, db_session, people):
    first = folder(db_session, people["admin"])
    second = folder(db_session, people["admin"], "Khác")
    empty = folder(db_session, people["admin"], "Trống")
    foreign = folder(db_session, people["other"])
    included = [
        make_document(db_session, people["admin"], folder_id=first.id, status=status)
        for status in ["queued", "failed", "deleting"]
    ]
    make_document(
        db_session,
        people["admin"],
        folder_id=first.id,
        status="deleted",
        deleted_at=datetime.now(UTC),
    )
    other = make_document(db_session, people["admin"], folder_id=second.id)
    unclassified = make_document(db_session, people["admin"])
    make_document(db_session, people["other"], folder_id=foreign.id)
    auth = headers(client, people["member"])
    response = client.get(f"/api/v1/documents?folder_id={first.id}", headers=auth)
    rows = response.json()["data"]["items"]
    assert {r["id"] for r in rows} == {str(doc.id) for doc in included}
    assert all(r["folder_id"] == str(first.id) for r in rows)
    limited = client.get(f"/api/v1/documents?folder_id={first.id}&limit=1", headers=auth)
    assert limited.json()["data"]["items"] == rows[:1]
    assert client.get(f"/api/v1/documents?folder_id={empty.id}", headers=auth).json()["data"] == {
        "items": []
    }
    all_rows = client.get("/api/v1/documents", headers=auth).json()["data"]["items"]
    assert {r["id"] for r in all_rows} == {str(doc.id) for doc in [*included, other, unclassified]}
    for target in [foreign.id, uuid.uuid4()]:
        rejected = client.get(f"/api/v1/documents?folder_id={target}", headers=auth)
        assert rejected.status_code == 404
        assert rejected.json()["error"]["code"] == "not_found"
    for target in ["", "null", "not-a-uuid"]:
        assert client.get(f"/api/v1/documents?folder_id={target}", headers=auth).status_code == 422
    assert client.get(f"/api/v1/documents?folder_id={first.id}").status_code == 401


def test_database_rejects_cross_workspace_update(db_session, people):
    doc = make_document(db_session, people["admin"])
    foreign = folder(db_session, people["other"])
    with pytest.raises(IntegrityError) as error, db_session.begin_nested():
        doc.folder_id = foreign.id
        db_session.flush()
    assert error.value.orig.diag.constraint_name == "fk_documents_folder_scope"
    db_session.refresh(doc)
    assert doc.folder_id is None


def test_upload_classifies_atomically_and_dedup_does_not_move_existing(
    client, db_session, people, storage
):
    first = folder(db_session, people["admin"])
    second = folder(db_session, people["admin"], "Khác")
    response = send(client, people["admin"], data={"folder_id": str(first.id)})
    assert response.status_code == 202
    result = response.json()["data"]
    doc = db_session.get(Document, uuid.UUID(result["document_id"]))
    assert doc.folder_id == first.id
    assert db_session.get(ProcessingJob, uuid.UUID(result["job_id"])).document_id == doc.id
    duplicate = send(client, people["admin"], data={"folder_id": str(second.id)})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "duplicate_document"
    db_session.refresh(doc)
    assert doc.folder_id == first.id
    assert len(list(storage.rglob("*.txt"))) == 1
    assert db_session.scalar(select(func.count()).select_from(ProcessingJob)) == 1
    assert db_session.scalar(select(func.count()).select_from(DocumentRevision)) == 1


@pytest.mark.parametrize("target", ["foreign", "missing"])
def test_upload_invalid_scope_leaves_no_file_metadata_or_job(
    client, db_session, people, storage, target
):
    target_id = folder(db_session, people["other"]).id if target == "foreign" else uuid.uuid4()
    response = send(client, people["admin"], data={"folder_id": str(target_id)})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert not list(storage.rglob("*.*"))
    for model in [Document, DocumentRevision, ProcessingJob]:
        assert db_session.scalar(select(func.count()).select_from(model)) == 0


@pytest.mark.parametrize(
    "fields",
    [
        [("folder_id", (None, ""))],
        [("folder_id", (None, "null"))],
        [("folder_id", (None, "bad"))],
        [("folder_id", (None, str(uuid.uuid4()))), ("folder_id", (None, str(uuid.uuid4())))],
        [("workspace_id", (None, str(uuid.uuid4())))],
        [("unexpected", (None, "x"))],
        [("folder_id", ("folder.txt", b"x", "text/plain"))],
        [("file", ("extra.txt", b"x", "text/plain"))],
    ],
)
def test_upload_rejects_invalid_duplicate_and_unknown_parts(
    client, db_session, people, storage, fields
):
    response = client.post(
        "/api/v1/documents",
        headers=headers(client, people["admin"]),
        files=[("file", ("policy.txt", b"Policy", "text/plain")), *fields],
    )
    assert response.status_code == 422
    assert not list(storage.rglob("*.*"))
    assert db_session.scalar(select(func.count()).select_from(Document)) == 0


def test_upload_folder_keeps_authorization_and_stream_limits(
    client, db_session, people, storage, monkeypatch
):
    target = folder(db_session, people["admin"])
    data = {"folder_id": str(target.id)}
    assert send(client, people["member"], data=data).status_code == 403
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    response = send(client, people["admin"], body=b"x" * (1024**2 + 1), data=data)
    assert response.status_code == 413
    assert not list(storage.rglob("*.*"))


def test_register_upload_checks_scope_for_non_api_callers(db_session, people, storage):
    foreign = folder(db_session, people["other"])
    path = storage / "test.txt"
    path.write_bytes(b"Policy")
    stored = StoredUpload(
        path, path.name, hashlib.sha256(b"Policy").hexdigest(), 6, uuid.uuid4(), uuid.uuid4()
    )
    with pytest.raises(AppError) as error:
        register_upload(db_session, people["admin"], path.name, "txt", stored, foreign.id)
    assert error.value.status_code == 404
    assert not path.exists()
    assert db_session.get(Document, stored.document_id) is None


@pytest.fixture
def committed_classification(db_engine):
    """Independent committed rows for two-session lock and stale-identity tests."""
    workspace_id, user_id = uuid.uuid4(), uuid.uuid4()
    person = SimpleNamespace(id=user_id, workspace_id=workspace_id)
    try:
        with Session(db_engine) as db, db.begin():
            db.add(Workspace(id=workspace_id, name="Classification isolation test"))
            db.flush()
            db.add(
                User(
                    id=user_id,
                    workspace_id=workspace_id,
                    username="class." + user_id.hex,
                    email=user_id.hex + "@example.invalid",
                    display_name="Test",
                    password_hash="unused-service-test",
                    role="knowledge_admin",
                )
            )
            db.flush()
            target = folder(db, person)
            doc = make_document(db, person)
            ids = target.id, doc.id
        yield db_engine, person, *ids
    finally:
        with Session(db_engine) as db, db.begin():
            db.execute(delete(Document).where(Document.workspace_id == workspace_id))
            db.execute(delete(Folder).where(Folder.workspace_id == workspace_id))
            db.execute(delete(User).where(User.id == user_id))
            db.execute(delete(Workspace).where(Workspace.id == workspace_id))


def test_move_reloads_lifecycle_after_another_transaction_deletes(committed_classification):
    engine, user, target_id, doc_id = committed_classification
    with Session(engine) as stale, Session(engine) as deleting:
        cached = stale.get(Document, doc_id)
        assert cached.status == "queued"
        current = deleting.get(Document, doc_id)
        current.status = "deleting"
        deleting.commit()
        with pytest.raises(AppError) as error:
            move_document(stale, doc_id, user, target_id)
        assert error.value.status_code == 410
        assert cached.status == "deleting" and cached.folder_id is None


def test_attachment_holds_folder_until_commit_then_blocks_delete(
    committed_classification, monkeypatch
):
    engine, user, target_id, doc_id = committed_classification
    with Session(engine) as moving, Session(engine) as removing:
        commit = moving.commit
        observed = []

        def before_commit():
            removing.execute(text("SET LOCAL lock_timeout='300ms'"))
            with pytest.raises(OperationalError) as error:
                delete_folder(removing, target_id, user)
            assert error.value.orig.sqlstate == "55P03"
            removing.rollback()
            observed.append("delete blocked before attachment commit")
            commit()

        monkeypatch.setattr(moving, "commit", before_commit)
        move_document(moving, doc_id, user, target_id)
        assert len(observed) == 1
        with pytest.raises(AppError) as error:
            delete_folder(removing, target_id, user)
        assert error.value.status_code == 409 and error.value.code == "folder_not_empty"


def test_move_waits_for_document_writer_and_rejects_committed_delete(committed_classification):
    engine, user, target_id, doc_id = committed_classification
    with Session(engine) as deleting, Session(engine) as moving:
        current = deleting.get(Document, doc_id, with_for_update=True)
        current.status = "deleting"
        deleting.flush()
        moving.execute(text("SET LOCAL lock_timeout='300ms'"))
        with pytest.raises(OperationalError) as blocked:
            move_document(moving, doc_id, user, target_id)
        assert blocked.value.orig.sqlstate == "55P03"
        moving.rollback()
        deleting.commit()
        with pytest.raises(AppError) as unavailable:
            move_document(moving, doc_id, user, target_id)
        assert unavailable.value.status_code == 410
        assert moving.get(Document, doc_id).folder_id is None
