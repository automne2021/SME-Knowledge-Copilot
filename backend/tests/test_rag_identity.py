"""Real PostgreSQL/API identity and scope contracts; no model calls."""

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy import select

from app.core.config import Settings
from app.core.security import AdminUser, hash_password, token_digest, verify_password
from app.main import create_app
from app.models import (
    AnswerCitation,
    AuthToken,
    ChatMessage,
    ChatSession,
    Chunk,
    Document,
    DocumentRevision,
    ProcessingJob,
    QueryRun,
    User,
)
from app.models.enums import DocumentStatus, UserRole
from app.seed import seed_demo

PASSWORD = "test-only-password-42"


def headers(client, person):
    response = client.post(
        "/api/v1/auth/login", json={"username": person.username, "password": PASSWORD}
    )
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["data"]["access_token"]}


def make_document(db, user, **kwargs):
    row = Document(
        workspace_id=user.workspace_id,
        created_by=user.id,
        filename="sample.txt",
        mime="text/plain",
        size_bytes=10,
        sha256=uuid.uuid4().hex * 2,
        **kwargs,
    )
    db.add(row)
    db.flush()
    return row


def test_login_and_me_persist_only_token_hash(client, db_session, people):
    response = client.post(
        "/api/v1/auth/login", json={"username": " TEST.MEMBER ", "password": PASSWORD}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["token_type"] == "bearer" and data["expires_in"] == 3600
    saved = db_session.scalar(select(AuthToken).where(AuthToken.user_id == people["member"].id))
    assert saved.token_hash == token_digest(data["access_token"])
    assert data["access_token"] != saved.token_hash
    me = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + data["access_token"]})
    assert me.status_code == 200
    assert set(me.json()["data"]) == {"id", "workspace_id", "username", "display_name", "role"}
    assert me.json()["data"]["role"] == "member"
    assert me.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("kind", ["wrong_password", "unknown", "inactive", "legacy"])
def test_login_failures_have_same_public_error(client, db_session, people, kind):
    person = people["member"]
    username, password = person.username, PASSWORD
    if kind == "wrong_password":
        password = "wrong"
    elif kind == "unknown":
        username = "test.unknown"
    elif kind == "inactive":
        person.is_active = False
        db_session.flush()
    else:
        username = people["legacy"].username
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert response.headers["www-authenticate"] == "Bearer"
    assert password not in response.text
    assert db_session.scalar(select(AuthToken)) is None


@pytest.mark.parametrize(
    "authorization", [None, "Basic not-bearer", "Bearer invalid", "Bearer " + "a" * 43]
)
def test_missing_malformed_unknown_token_is_401(client, authorization):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": authorization} if authorization else {}
    )
    assert response.status_code == 401


@pytest.mark.parametrize("state", ["expired", "revoked", "inactive", "role_changed"])
def test_token_state_is_revalidated(client, db_session, people, state):
    auth = headers(client, people["member"])
    token = db_session.scalar(select(AuthToken))
    if state == "expired":
        token.created_at = datetime.now(UTC) - timedelta(hours=2)
        token.expires_at = datetime.now(UTC) - timedelta(hours=1)
    elif state == "revoked":
        token.revoked_at = datetime.now(UTC)
    elif state == "inactive":
        people["member"].is_active = False
    else:
        people["member"].role = UserRole.DEMO_ADMIN
    db_session.flush()
    assert client.get("/api/v1/auth/me", headers=auth).status_code == 401


def test_client_cannot_inject_identity_or_role(client, people):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": people["member"].username,
            "password": PASSWORD,
            "role": "knowledge_admin",
            "workspace_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 422
    assert PASSWORD not in response.text


def test_admin_dependency_denies_member_through_http(db_session, people):
    from app.core.db import get_db

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session

    @app.post("/test-admin-contract")
    def protected(user: AdminUser):
        return {"role": user.role}

    with TestClient(app) as api:
        member_auth = headers(api, people["member"])
        admin_auth = headers(api, people["admin"])
        assert api.post("/test-admin-contract", headers=member_auth).status_code == 403
        assert api.post("/test-admin-contract", headers=admin_auth).status_code == 200
        assert api.post("/test-admin-contract").status_code == 401


def test_documents_are_workspace_scoped_and_deleted_checked_after_scope(client, db_session, people):
    own = make_document(db_session, people["member"])
    foreign = make_document(db_session, people["other"])
    foreign.status = DocumentStatus.DELETED
    foreign.deleted_at = datetime.now(UTC)
    db_session.flush()
    auth = headers(client, people["member"])
    assert client.get(f"/api/v1/documents/{own.id}", headers=auth).status_code == 200
    for document_id in [foreign.id, uuid.uuid4()]:
        response = client.get(f"/api/v1/documents/{document_id}", headers=auth)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"
    listing = client.get(
        "/api/v1/documents?workspace_id=" + str(foreign.workspace_id), headers=auth
    )
    assert [row["id"] for row in listing.json()["data"]["items"]] == [str(own.id)]
    own.status = DocumentStatus.DELETING
    db_session.flush()
    assert client.get(f"/api/v1/documents/{own.id}", headers=auth).status_code == 410
    assert "storage_key" not in listing.text


def test_session_owner_including_admin_and_runs(client, db_session, people):
    member_auth, admin_auth = headers(client, people["member"]), headers(client, people["admin"])
    response = client.post(
        "/api/v1/chat/sessions", headers=member_auth, json={"title": "My session"}
    )
    assert response.status_code == 201
    session_id = response.json()["data"]["id"]
    run = QueryRun(
        session_id=uuid.UUID(session_id),
        client_request_id=uuid.uuid4(),
        input_hash="a" * 64,
        question="A question",
    )
    db_session.add(run)
    db_session.flush()
    for auth in [admin_auth, headers(client, people["other"])]:
        assert (
            client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=auth).status_code
            == 404
        )
        assert client.get(f"/api/v1/chat/runs/{run.id}", headers=auth).status_code == 404
        assert client.get("/api/v1/chat/sessions", headers=auth).json()["data"]["items"] == []
    assert client.get(f"/api/v1/chat/runs/{run.id}", headers=member_auth).status_code == 200
    assert (
        client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=member_auth).json()[
            "data"
        ]["items"]
        == []
    )
    injected = client.post(
        "/api/v1/chat/sessions",
        headers=member_auth,
        json={"title": "other", "created_by": str(people["admin"].id)},
    )
    assert injected.status_code == 422


def test_jobs_scope_does_not_expose_legacy_or_foreign_jobs(client, db_session, people):
    own, foreign = (
        make_document(db_session, people["member"]),
        make_document(db_session, people["other"]),
    )
    rows = []
    for doc in [own, foreign]:
        row = ProcessingJob(
            document_id=doc.id, entity_type="document", entity_id=doc.id, kind="ingest"
        )
        db_session.add(row)
        rows.append(row)
    legacy = ProcessingJob(entity_type="meeting", entity_id=uuid.uuid4())
    db_session.add(legacy)
    db_session.flush()
    auth = headers(client, people["member"])
    assert client.get(f"/api/v1/jobs/{rows[0].id}", headers=auth).status_code == 200
    for row in [rows[1], legacy]:
        assert client.get(f"/api/v1/jobs/{row.id}", headers=auth).status_code == 404


def test_seed_is_idempotent_and_never_promotes_existing_user(db_session):
    config = SimpleNamespace(
        demo_admin_password=SecretStr("admin-only-test-password"),
        demo_member_password=SecretStr("member-only-test-password"),
    )
    result = seed_demo(db_session, config)
    assert result["users_created"] == 2
    admin = db_session.scalar(select(User).where(User.username == "demo.admin"))
    old_hash = admin.password_hash
    assert verify_password(old_hash, config.demo_admin_password.get_secret_value())
    config.demo_admin_password = SecretStr("different-admin-password")
    assert seed_demo(db_session, config)["users_created"] == 0
    assert admin.password_hash == old_hash
    admin.role = UserRole.MEMBER
    db_session.flush()
    with pytest.raises(ValueError, match="Seed identity conflict"):
        seed_demo(db_session, config)


@pytest.mark.parametrize("ttl", [0, -1, 86401])
def test_invalid_auth_config_is_rejected(ttl):
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://u:p@localhost/db",
            auth_token_ttl_seconds=ttl,
        )


def test_password_hash_is_salted_and_invalid_hash_is_safe():
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)
    assert first != second and first.startswith("$argon2id$")
    assert verify_password(first, PASSWORD)
    assert not verify_password(first, "incorrect")
    assert not verify_password("legacy-placeholder", PASSWORD)


@pytest.mark.parametrize(
    "source_change",
    ["deleting", "chunk_removed", "generation_mismatch", "revision_failed", "citation_unavailable"],
)
def test_history_revalidates_sources_before_cleanup_flag(client, db_session, people, source_change):
    person = people["member"]
    doc = make_document(db_session, person)
    revision = DocumentRevision(
        document_id=doc.id,
        version=1,
        storage_key="private/internal",
        status="ready",
        expected_chunk_count=1,
    )
    db_session.add(revision)
    db_session.flush()
    generation = uuid.uuid4()
    source = Chunk(
        revision_id=revision.id,
        generation_id=generation,
        chunk_index=0,
        text="source fact",
        text_sha256="a" * 64,
        location_json={},
        source_spans_json=[],
        vector_point_id=uuid.uuid4(),
        token_count=3,
    )
    doc.active_revision_id = revision.id
    doc.active_generation_id = generation
    doc.status = "ready"
    session = ChatSession(workspace_id=person.workspace_id, created_by=person.id)
    db_session.add_all([source, session])
    db_session.flush()
    run = QueryRun(
        session_id=session.id,
        client_request_id=uuid.uuid4(),
        input_hash="a" * 64,
        question="Question",
        status="completed",
    )
    db_session.add(run)
    db_session.flush()
    message = ChatMessage(
        session_id=session.id,
        query_run_id=run.id,
        role="assistant",
        content="Source answer",
        answer_status="grounded",
    )
    db_session.add(message)
    db_session.flush()
    citation = AnswerCitation(
        message_id=message.id,
        chunk_id=source.id,
        document_id=doc.id,
        revision_id=revision.id,
        generation_id=generation,
        evidence_id="E1",
        location_snapshot={},
        excerpt_snapshot="private source excerpt",
    )
    db_session.add(citation)
    db_session.flush()
    auth = headers(client, person)
    path = f"/api/v1/chat/sessions/{session.id}/messages"
    assert client.get(path, headers=auth).json()["data"]["items"][0]["content"] == "Source answer"
    if source_change == "deleting":
        doc.status = "deleting"
    elif source_change == "chunk_removed":
        db_session.delete(source)
    elif source_change == "generation_mismatch":
        citation.generation_id = uuid.uuid4()
    elif source_change == "revision_failed":
        revision.status = "failed"
    else:
        citation.source_status = "unavailable"
    db_session.flush()
    assert message.source_unavailable is False
    response = client.get(path, headers=auth)
    assert response.json()["data"]["items"][0]["content"] == ""
    assert response.json()["data"]["items"][0]["source_unavailable"] is True
    assert "private source excerpt" not in response.text


@pytest.mark.parametrize(
    "path",
    [
        "/documents",
        "/documents/{}",
        "/jobs/{}",
        "/chat/sessions",
        "/chat/sessions/{}/messages",
        "/chat/runs/{}",
    ],
)
def test_resource_endpoints_require_identity(client, path):
    response = client.get("/api/v1" + path.format(uuid.uuid4()))
    assert response.status_code == 401


def test_unhandled_error_keeps_request_id_without_leaking_exception(caplog):
    app = create_app()

    @app.get("/test-failure-contract")
    def failure():
        raise RuntimeError("sensitive-password-or-token")

    with TestClient(app, raise_server_exceptions=False) as api:
        response = api.get(
            "/test-failure-contract", headers={"X-Request-ID": "untrusted-client-id"}
        )
    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == response.json()["request_id"]
    assert response.headers["X-Request-ID"] != "untrusted-client-id"
    assert response.json()["error"]["code"] == "internal_error"
    assert "sensitive-password-or-token" not in response.text
    assert "sensitive-password-or-token" not in caplog.text
