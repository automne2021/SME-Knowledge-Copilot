"""Search/source contracts: real SQL/Qdrant, labeled fake embeddings, no LLM."""

import threading
import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import hash_password
from app.main import create_app
from app.models import AuthToken, Chunk, Document, DocumentRevision, User, Workspace
from app.services.worker_errors import WorkerError
from tests.test_parsing_chunking import MANIFEST, SNAPSHOT


class QueryCounter:
    def count_query(self, text):
        return len(text) + 4  # fake counter to exercise the budget branch


class QueryEmbedder:
    def __init__(self):
        self.calls = []

    def encode_query(self, text):
        self.calls.append(text)
        return [1.0] + [0.0] * 383


@pytest.fixture
def search_env(worker_env, monkeypatch):
    env = worker_env
    settings = get_settings()
    monkeypatch.setattr(settings, "storage_dir", env.settings.storage_dir)
    monkeypatch.setattr(settings, "retrieval_score_threshold", None)
    with env.sessions() as db:
        user = db.get(User, env.user.id)
        user.password_hash = hash_password("search-test-only-password")
        username = user.username
        db.commit()
    app = create_app()

    def sessions():
        with env.sessions() as db:
            yield db

    app.dependency_overrides[get_db] = sessions
    runtime = SimpleNamespace(
        profile=env.profile,
        vector=env.vector,
        embedder=QueryEmbedder(),
        counter=QueryCounter(),
        lock=threading.Lock(),
        close=lambda: None,
    )
    app.state.search_runtime = runtime
    env.runtime = runtime
    with TestClient(app) as client:
        env.client = client
        login = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "search-test-only-password"},
        )
        assert login.status_code == 200
        env.auth = {"Authorization": "Bearer " + login.json()["data"]["access_token"]}
        env.search = lambda **payload: client.post(
            "/api/v1/search", headers=env.auth, json={"query": "policy"} | payload
        )
        try:
            yield env
        finally:
            with env.sessions() as db:
                db.execute(delete(AuthToken).where(AuthToken.user_id == env.user.id))
                db.commit()


def ready(env, body=b"A sample policy condition.", extension="txt"):
    uploaded = env.upload(body, extension)
    assert env.worker().run_once()["status"] == "completed"
    return uploaded


def test_empty_scope_does_not_call_embedding_or_qdrant(search_env, monkeypatch):
    env = search_env

    def forbidden(*args):
        raise AssertionError("empty scope must not initialize model/vector runtime")

    monkeypatch.setattr(env.vector, "query", forbidden)
    response = env.search()
    assert response.status_code == 200
    assert response.json()["data"]["hits"] == []
    assert response.json()["data"]["reason_code"] == "no_ready_documents"
    assert not env.runtime.embedder.calls


def test_member_search_uses_sql_text_and_stable_ranking(search_env, monkeypatch):
    env = search_env
    ready(env, b"Policy one.")
    ready(env, b"Policy two.")
    with env.sessions() as db:
        db.get(User, env.user.id).role = "member"
        db.commit()
    original = env.vector.query

    def poisoned(*args):
        points = original(*args)
        for point in points:
            point["payload"].update(text="FORGED", file_name="wrong", location={"page_start": 999})
        return points + [points[0]]

    monkeypatch.setattr(env.vector, "query", poisoned)
    response = env.search(query="  policy  ")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["hits"]) == 2 and data["trace"]["duplicate_count"] == 1
    assert [hit["chunk_id"] for hit in data["hits"]] == sorted(
        hit["chunk_id"] for hit in data["hits"]
    )
    assert {hit["excerpt"] for hit in data["hits"]} == {"Policy one.", "Policy two."}
    assert all(hit["source"]["file_name"] == "source.txt" for hit in data["hits"])
    assert all(hit["score_type"] == "cosine_similarity" for hit in data["hits"])
    assert env.runtime.embedder.calls == ["policy"]
    assert data["trace"]["candidate_k"] == 20 and data["trace"]["requested_top_k"] == 5
    assert data["trace"]["score_threshold"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "  "},
        {"query": "x" * 4001},
        {"query": 1},
        {"top_k": 0},
        {"top_k": 11},
        {"top_k": True},
        {"top_k": 2.5},
        {"workspace_id": str(uuid.uuid4())},
        {"filters": {"tags": ["not-p0"]}},
        {"filters": {"document_ids": ["not-a-uuid"]}},
        {"filters": {"document_ids": [str(uuid.uuid4()) for _ in range(51)]}},
    ],
)
def test_search_validation_is_strict(search_env, payload):
    assert search_env.search(**payload).status_code == 422
    assert not search_env.runtime.embedder.calls


def test_mode_and_embedding_token_limit_and_capacity(search_env):
    env = search_env
    ready(env)
    mode = env.search(mode="hybrid")
    assert mode.status_code == 422 and mode.json()["error"]["code"] == "unsupported_retrieval_mode"
    long_query = env.search(query="x" * 600)
    assert (
        long_query.status_code == 422 and long_query.json()["error"]["code"] == "question_too_long"
    )
    assert not env.runtime.embedder.calls
    env.runtime.lock.acquire()
    try:
        assert env.search().status_code == 429
    finally:
        env.runtime.lock.release()


def test_nonready_explicit_filter_and_foreign_id_all_fail_closed(search_env):
    env = search_env
    pending = env.upload()
    own_id = str(pending["document_id"])
    foreign_workspace, foreign_user, foreign_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    with env.sessions() as db:
        db.add(Workspace(id=foreign_workspace, name="Foreign test scope"))
        db.flush()
        db.add(
            User(
                id=foreign_user,
                workspace_id=foreign_workspace,
                username="foreign." + foreign_user.hex,
                email=foreign_user.hex + "@example.invalid",
                display_name="Foreign",
                role="member",
                password_hash="not-used",
            )
        )
        db.flush()
        db.add(
            Document(
                id=foreign_id,
                workspace_id=foreign_workspace,
                created_by=foreign_user,
                filename="hidden.txt",
                mime="text/plain",
                size_bytes=1,
                sha256="a" * 64,
            )
        )
        db.commit()
    try:
        assert env.search(filters={"document_ids": [own_id]}).status_code == 409
        response = env.search(filters={"document_ids": [own_id, str(foreign_id)]})
        assert response.status_code == 404 and "hidden.txt" not in response.text
        assert (
            env.client.get(f"/api/v1/documents/{foreign_id}/content", headers=env.auth).status_code
            == 404
        )
        assert env.search(filters={"document_ids": [own_id, own_id]}).status_code == 422
        assert not env.runtime.embedder.calls
    finally:
        with env.sessions() as db:
            db.execute(delete(Document).where(Document.id == foreign_id))
            db.execute(delete(User).where(User.id == foreign_user))
            db.execute(delete(Workspace).where(Workspace.id == foreign_workspace))
            db.commit()


def test_document_filter_and_real_qdrant_scope_exclude_orphan_points(search_env):
    env = search_env
    first, second = ready(env, b"First policy."), ready(env, b"Second policy.")
    with env.sessions() as db:
        active_generation = str(db.get(Document, first["document_id"]).active_generation_id)
    stray = [
        {
            "id": str(uuid.uuid4()),
            "vector": [1.0] + [0.0] * 383,
            "payload": {
                "workspace_id": str(env.user.workspace_id),
                "generation_id": str(uuid.uuid4()),
                "index_version": env.profile["index_version"],
            },
        },
        {
            "id": str(uuid.uuid4()),
            "vector": [1.0] + [0.0] * 383,
            "payload": {
                "workspace_id": str(uuid.uuid4()),
                "generation_id": active_generation,
                "index_version": env.profile["index_version"],
            },
        },
    ]
    stray.append(
        {
            "id": str(uuid.uuid4()),
            "vector": [1.0] + [0.0] * 383,
            "payload": {
                "workspace_id": str(env.user.workspace_id),
                "generation_id": active_generation,
                "index_version": "wrong-index",
            },
        }
    )
    env.vector.upsert(stray)
    response = env.search(filters={"document_ids": [str(first["document_id"])]})
    assert response.status_code == 200
    data = response.json()["data"]
    assert {hit["document_id"] for hit in data["hits"]} == {str(first["document_id"])}
    assert data["trace"]["candidate_count"] == 1 and data["trace"]["sql_rejected_count"] == 0
    assert str(second["document_id"]) not in response.text


def test_delete_race_after_vector_query_revalidates_sql(search_env, monkeypatch):
    env = search_env
    uploaded = ready(env)
    original = env.vector.query

    def delete_during_query(*args):
        result = original(*args)
        with env.sessions() as db:
            document = db.get(Document, uploaded["document_id"])
            document.status, document.lifecycle_version = "deleting", document.lifecycle_version + 1
            db.commit()
        return result

    monkeypatch.setattr(env.vector, "query", delete_during_query)
    response = env.search()
    assert response.status_code == 200
    assert response.json()["data"]["hits"] == []
    assert response.json()["data"]["trace"]["sql_rejected_count"] == 1
    assert env.search(filters={"document_ids": [str(uploaded["document_id"])]}).status_code == 410


@pytest.mark.parametrize(
    "failure", ["vector_timeout", "vector_fingerprint_mismatch", "invalid_embedding"]
)
def test_technical_failure_is_not_empty_success(search_env, monkeypatch, failure):
    env = search_env
    ready(env)

    def fail(*args):
        raise WorkerError(failure, True)

    monkeypatch.setattr(env.vector, "query", fail)
    response = env.search()
    assert (
        response.status_code == 503 and response.json()["error"]["code"] == "retrieval_unavailable"
    )
    assert "hits" not in response.json()


def test_missing_and_forged_candidates_are_sql_rejected(search_env, monkeypatch):
    env = search_env
    ready(env)
    original = env.vector.query

    def forged(*args):
        points = original(*args)
        points[0]["payload"]["chunk_id"] = str(uuid.uuid4())
        points.append({"id": str(uuid.uuid4()), "score": 0.9, "payload": {}})
        return points

    monkeypatch.setattr(env.vector, "query", forged)
    response = env.search()
    assert response.status_code == 200 and not response.json()["data"]["hits"]
    assert response.json()["data"]["trace"]["sql_rejected_count"] == 2


def test_plaintext_source_is_literal_and_inactive_chunk_unavailable(search_env):
    env = search_env
    uploaded = ready(env, "# Quy định\r\n<script>alert(1)</script>\r\n".encode(), "md")
    document_id = uploaded["document_id"]
    hits = env.search().json()["data"]["hits"]
    chunk = env.client.get(hits[0]["source"]["chunk_url"], headers=env.auth)
    assert chunk.status_code == 200 and chunk.json()["data"]["source_spans"]
    response = env.client.get(f"/api/v1/documents/{document_id}/content", headers=env.auth)
    assert response.status_code == 200 and response.headers["content-type"].startswith("text/plain")
    assert "<script>alert(1)</script>" in response.text
    assert (
        response.headers["x-content-type-options"] == "nosniff"
        and response.headers["cache-control"] == "no-store"
    )
    assert env.client.get(hits[0]["source"]["chunk_url"]).status_code == 401
    with env.sessions() as db:
        chunk_row = db.get(Chunk, uuid.UUID(hits[0]["chunk_id"]))
        chunk_row.generation_id = uuid.uuid4()
        db.commit()
    assert env.client.get(hits[0]["source"]["chunk_url"], headers=env.auth).status_code == 410


@pytest.mark.parametrize("ref", ["acceptance", "leave"])
def test_pdf_bytes_and_docx_extracted_text_source(search_env, ref):
    env = search_env
    entry = next(item for item in MANIFEST["documents"] if item["document_id"] == ref)
    raw = (SNAPSHOT / entry["path"]).read_bytes()
    uploaded = ready(env, raw, entry["format"])
    url = f"/api/v1/documents/{uploaded['document_id']}/content"
    response = env.client.get(url, headers=env.auth | {"Range": "bytes=0-99"})
    assert response.status_code == 200 and "accept-ranges" not in response.headers
    assert env.client.get(url, headers={"Range": "bytes=0-99"}).status_code == 401
    if ref == "acceptance":
        assert response.content == raw and response.headers["content-type"] == "application/pdf"
    else:
        assert response.headers["content-type"].startswith("text/plain") and "12" in response.text
        assert "page_start" not in response.text


def test_source_storage_escape_and_checksum_change_are_not_served(search_env):
    env = search_env
    uploaded = ready(env)
    url = f"/api/v1/documents/{uploaded['document_id']}/content"
    with env.sessions() as db:
        document = db.get(Document, uploaded["document_id"])
        revision = db.get(DocumentRevision, document.active_revision_id)
        path = env.settings.storage_dir / revision.storage_key
        path.write_bytes(b"x" * path.stat().st_size)
    assert env.client.get(url, headers=env.auth).status_code == 410
    with env.sessions() as db:
        db.get(DocumentRevision, revision.id).storage_key = "../../.env"
        db.commit()
    response = env.client.get(url, headers=env.auth)
    assert response.status_code == 410 and "storage_key" not in response.text
