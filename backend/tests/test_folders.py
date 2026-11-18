"""Folder CRUD and constraints on real PostgreSQL; no model calls."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.models import Document, DocumentRevision, Folder
from tests.test_rag_identity import headers, make_document


def create(client, auth, name="Nhân sự"):
    response = client.post("/api/v1/folders", headers=auth, json={"name": name})
    assert response.status_code == 201
    return response.json()["data"]


def folder(db, person, name="Nhân sự"):
    row = Folder(workspace_id=person.workspace_id, created_by=person.id, name=name)
    db.add(row)
    db.flush()
    return row


def test_admin_crud_and_member_listing(client, db_session, people):
    admin = headers(client, people["admin"])
    member = headers(client, people["member"])
    assert client.get("/api/v1/folders", headers=member).json()["data"] == {"items": []}
    row = create(client, admin, "  Nhân sự  ")
    assert row["name"] == "Nhân sự" and row["ready_document_count"] == 0
    assert row["created_at"] and row["updated_at"]
    stored = db_session.get(Folder, uuid.UUID(row["id"]))
    assert stored.created_by == people["admin"].id
    assert stored.workspace_id == people["admin"].workspace_id
    response = client.get("/api/v1/folders", headers=member)
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.json()["data"]["items"] == [row]
    renamed = client.patch(
        f"/api/v1/folders/{row['id']}", headers=admin, json={"name": "  Kỹ thuật  "}
    )
    assert renamed.status_code == 200
    assert renamed.json()["data"]["name"] == "Kỹ thuật"
    # Renaming to the same value is allowed.
    assert (
        client.patch(
            f"/api/v1/folders/{row['id']}", headers=admin, json={"name": "Kỹ thuật"}
        ).status_code
        == 200
    )
    removed = client.delete(f"/api/v1/folders/{row['id']}", headers=admin)
    assert removed.status_code == 200
    assert removed.json()["data"] == {"id": row["id"], "deleted": True}
    assert client.get("/api/v1/folders", headers=member).json()["data"]["items"] == []
    assert client.delete(f"/api/v1/folders/{row['id']}", headers=admin).status_code == 404


def test_duplicate_create_and_rename_are_case_insensitive_409(client, people):
    auth = headers(client, people["admin"])
    first = create(client, auth, "Nhân Sự")
    other = create(client, auth, "Kế toán")
    duplicate = client.post("/api/v1/folders", headers=auth, json={"name": "  NHÂN SỰ  "})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "duplicate_folder"
    renamed = client.patch(f"/api/v1/folders/{other['id']}", headers=auth, json={"name": "nhân sự"})
    assert renamed.status_code == 409
    assert renamed.json()["error"]["code"] == "duplicate_folder"
    listing = client.get("/api/v1/folders", headers=auth).json()["data"]["items"]
    assert {row["id"]: row["name"] for row in listing} == {
        first["id"]: "Nhân Sự",
        other["id"]: "Kế toán",
    }


@pytest.mark.parametrize("method", ["post", "patch", "delete"])
def test_member_cannot_write(client, db_session, people, method):
    row = folder(db_session, people["admin"])
    auth = headers(client, people["member"])
    path = "/api/v1/folders" + ("" if method == "post" else f"/{row.id}")
    kwargs = {} if method == "delete" else {"json": {"name": "Kinh doanh"}}
    response = getattr(client, method)(path, headers=auth, **kwargs)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_identity_is_required(client, method):
    path = "/api/v1/folders" + (f"/{uuid.uuid4()}" if method in {"patch", "delete"} else "")
    kwargs = {"json": {"name": "X"}} if method in {"post", "patch"} else {}
    assert getattr(client, method)(path, **kwargs).status_code == 401


def test_workspace_scope_and_same_name_in_other_workspace(client, db_session, people):
    foreign = folder(db_session, people["other"])
    auth = headers(client, people["admin"])
    assert client.get("/api/v1/folders", headers=auth).json()["data"]["items"] == []
    create(client, auth)  # The same name in another workspace is legal.
    for target in [foreign.id, uuid.uuid4()]:
        for method in ["patch", "delete"]:
            kwargs = {"json": {"name": "Changed"}} if method == "patch" else {}
            response = getattr(client, method)(f"/api/v1/folders/{target}", headers=auth, **kwargs)
            assert response.status_code == 404
            assert response.json()["error"]["code"] == "not_found"
    db_session.refresh(foreign)
    assert foreign.name == "Nhân sự"


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": ""},
        {"name": " \t\n "},
        {"name": "x" * 101},
        {"name": 12},
        {"name": None},
        {"name": "X", "workspace_id": str(uuid.uuid4())},
        {"name": "X", "created_by": str(uuid.uuid4())},
        {"name": "X", "parent_id": None},
    ],
)
def test_name_validation_for_create_and_rename(client, db_session, people, body):
    row = folder(db_session, people["admin"])
    auth = headers(client, people["admin"])
    assert client.post("/api/v1/folders", headers=auth, json=body).status_code == 422
    assert client.patch(f"/api/v1/folders/{row.id}", headers=auth, json=body).status_code == 422
    db_session.refresh(row)
    assert row.name == "Nhân sự"


def test_name_length_boundaries(client, people):
    auth = headers(client, people["admin"])
    assert create(client, auth, "Đ")["name"] == "Đ"
    assert create(client, auth, "ệ" * 100)["name"] == "ệ" * 100


@pytest.mark.parametrize(
    "status", ["queued", "processing", "failed", "needs_ocr", "deleting", "deleted"]
)
def test_nonempty_folder_cannot_be_deleted_even_without_ready_documents(
    client, db_session, people, status
):
    row = folder(db_session, people["admin"])
    doc = make_document(
        db_session,
        people["admin"],
        folder_id=row.id,
        status=status,
        deleted_at=datetime.now(UTC) if status == "deleted" else None,
    )
    auth = headers(client, people["admin"])
    response = client.delete(f"/api/v1/folders/{row.id}", headers=auth)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "folder_not_empty"
    listing = client.get("/api/v1/folders", headers=auth).json()["data"]["items"]
    assert listing[0]["ready_document_count"] == 0
    assert db_session.scalar(select(Document.folder_id).where(Document.id == doc.id)) == row.id


def test_ready_counts_exclude_other_statuses_unclassified_and_foreign_documents(
    client, db_session, people
):
    own = folder(db_session, people["admin"])
    empty = folder(db_session, people["admin"], "Trống")
    foreign = folder(db_session, people["other"])
    for person, target in [
        (people["admin"], own),
        (people["other"], foreign),
        (people["admin"], None),
    ]:
        doc = make_document(db_session, person, folder_id=target.id if target else None)
        revision = DocumentRevision(document_id=doc.id, version=1, storage_key="test-only")
        db_session.add(revision)
        db_session.flush()
        doc.status, doc.active_revision_id, doc.active_generation_id = (
            "ready",
            revision.id,
            uuid.uuid4(),
        )
        db_session.flush()
    make_document(db_session, people["admin"], folder_id=own.id, status="failed")
    auth = headers(client, people["member"])
    rows = client.get("/api/v1/folders", headers=auth).json()["data"]["items"]
    assert {r["id"]: r["ready_document_count"] for r in rows} == {str(own.id): 1, str(empty.id): 0}
    admin = headers(client, people["admin"])
    renamed = client.patch(f"/api/v1/folders/{own.id}", headers=admin, json={"name": "Mới"})
    assert renamed.json()["data"]["ready_document_count"] == 1
    assert client.delete(f"/api/v1/folders/{own.id}", headers=admin).status_code == 409


@pytest.mark.parametrize(
    "kind", ["creator_scope", "document_scope", "duplicate", "blank", "untrimmed"]
)
def test_database_rejects_invalid_folder_data(db_session, people, kind):
    row = folder(db_session, people["admin"])
    with pytest.raises(IntegrityError), db_session.begin_nested():
        if kind == "document_scope":
            make_document(db_session, people["other"], folder_id=row.id)
        else:
            db_session.add(
                Folder(
                    workspace_id=row.workspace_id,
                    created_by=people["other"].id
                    if kind == "creator_scope"
                    else people["admin"].id,
                    name={"duplicate": "NHÂN SỰ", "blank": "", "untrimmed": " X "}.get(kind, "X"),
                )
            )
            db_session.flush()


def test_database_delete_sets_only_folder_id_null_and_preserves_document(db_session, people):
    row = folder(db_session, people["admin"])
    doc = make_document(db_session, people["admin"], folder_id=row.id)
    doc_id, workspace_id = doc.id, doc.workspace_id
    db_session.execute(delete(Folder).where(Folder.id == row.id))
    db_session.expire_all()
    stored = db_session.get(Document, doc_id)
    assert stored.folder_id is None
    assert stored.workspace_id == workspace_id
    assert stored.filename == "sample.txt"
