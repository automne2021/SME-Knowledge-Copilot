"""Folder search/chat through real PostgreSQL/Qdrant; labeled fake inference only."""

import threading
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import delete

from app.models import Document, Folder, QueryRun, User, Workspace
from app.schemas.answer import ChatQuery
from app.services.chat import input_hash
from app.services.embeddings import content_hash
from app.services.retrieval import search
from tests.chat_support import ready


@pytest.fixture
def folder_qa(chat_env, monkeypatch):
    env = chat_env
    monkeypatch.setattr("app.services.chat.search", search)
    env.embedding_calls = []

    def encode(query, deadline=None):
        env.embedding_calls.append(query)
        return [1.0] + [0.0] * 383

    env.app.state.search_runtime = SimpleNamespace(
        profile=env.profile,
        vector=env.vector,
        embedder=SimpleNamespace(encode_query=encode),
        counter=SimpleNamespace(count_query=lambda text: 10),
        lock=threading.Lock(),
        close=lambda: None,
    )
    env.app.state.rag_settings = env.settings
    env.folders = []
    for name in ("Nhân sự", "Kỹ thuật", "Trống"):
        response = env.client.post("/api/v1/folders", headers=env.auth, json={"name": name})
        assert response.status_code == 201, response.text
        env.folders.append(response.json()["data"]["id"])
    foreign_workspace, foreign_user, foreign_folder = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    with env.sessions() as db:
        db.add(Workspace(id=foreign_workspace, name="Foreign folder test"))
        db.flush()
        db.add(
            User(
                id=foreign_user,
                workspace_id=foreign_workspace,
                username="folder." + foreign_user.hex,
                email=foreign_user.hex + "@example.invalid",
                display_name="Foreign",
                role="member",
                password_hash="unused-test-only",
            )
        )
        db.flush()
        db.add(
            Folder(
                id=foreign_folder,
                workspace_id=foreign_workspace,
                created_by=foreign_user,
                name="Hidden folder",
            )
        )
        db.commit()
    env.foreign_folder = str(foreign_folder)

    def request(endpoint, filters):
        if endpoint == "chat":
            return env.ask(filters=filters, client_request_id=str(uuid.uuid4()))
        return env.client.post(
            "/api/v1/search", headers=env.auth, json={"query": "policy", "filters": filters}
        )

    env.scoped = request

    def move(document_id, folder_id):
        response = env.client.patch(
            f"/api/v1/documents/{document_id}",
            headers=env.auth,
            json={"folder_id": folder_id},
        )
        assert response.status_code == 200, response.text

    env.move = move
    try:
        yield env
    finally:
        # These folders reference the worker user; remove before its fixture teardown.
        with env.sessions() as db:
            db.execute(
                delete(Folder).where(
                    Folder.workspace_id.in_([env.user.workspace_id, foreign_workspace])
                )
            )
            db.execute(delete(User).where(User.id == foreign_user))
            db.execute(delete(Workspace).where(Workspace.id == foreign_workspace))
            db.commit()


def document_ids(response, endpoint):
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    rows = data["hits"] if endpoint == "search" else data["citations"]
    return {row["document_id"] for row in rows}


@pytest.mark.parametrize("endpoint", ["search", "chat"])
def test_folder_scope_intersection_and_move_between_queries(folder_qa, endpoint):
    env = folder_qa
    first, second, empty = env.folders
    doc1 = str(ready(env, b"First policy.")["document_id"])
    doc2 = str(ready(env, b"Second policy.")["document_id"])
    env.move(doc1, first)
    env.move(doc2, second)
    selected = env.scoped(endpoint, {"folder_ids": [first]})
    assert document_ids(selected, endpoint) == {doc1}
    if endpoint == "chat":
        with env.sessions() as db:
            run = db.get(QueryRun, uuid.UUID(selected.json()["data"]["run_id"]))
            assert {row["document_id"] for row in run.retrieval_trace_json["evidence_map"]} == {
                doc1
            }
    both = env.scoped(endpoint, {"folder_ids": [first, second], "document_ids": [doc2]})
    assert document_ids(both, endpoint) == {doc2}
    disjoint = env.scoped(endpoint, {"folder_ids": [first], "document_ids": [doc2]})
    assert document_ids(disjoint, endpoint) == set()
    assert disjoint.json()["data"]["reason_code"] == "no_ready_documents"
    env.move(doc1, second)
    assert document_ids(env.scoped(endpoint, {"folder_ids": [first]}), endpoint) == set()
    # Search returns the union; the fake chat provider deliberately cites E1 only.
    union = env.scoped(endpoint, {"folder_ids": [second]})
    assert document_ids(union, endpoint) <= {doc1, doc2}
    assert document_ids(union, endpoint)
    if endpoint == "search":
        assert document_ids(union, endpoint) == {doc1, doc2}
    else:
        with env.sessions() as db:
            run = db.get(QueryRun, uuid.UUID(union.json()["data"]["run_id"]))
            assert set(run.config_json["resolved_document_ids"]) == {doc1, doc2}
    env.move(doc2, None)
    assert document_ids(env.scoped(endpoint, {"folder_ids": [second]}), endpoint) == {doc1}


@pytest.mark.parametrize("endpoint", ["search", "chat"])
@pytest.mark.parametrize("kind", ["missing", "foreign", "mixed"])
def test_folder_scope_rejects_whole_request_before_inference(folder_qa, endpoint, kind):
    env = folder_qa
    ids = [str(uuid.uuid4())] if kind == "missing" else [env.foreign_folder]
    if kind == "mixed":
        ids.insert(0, env.folders[0])
    response = env.scoped(endpoint, {"folder_ids": ids})
    assert response.status_code == 404, response.text
    assert response.json()["error"]["code"] == "not_found"
    assert "Hidden folder" not in response.text
    assert not env.embedding_calls and not env.provider.calls and not env.provider.counts


@pytest.mark.parametrize("endpoint", ["search", "chat"])
@pytest.mark.parametrize("pending", [False, True])
def test_empty_or_nonready_folder_abstains_without_inference(folder_qa, endpoint, pending):
    env = folder_qa
    if pending:
        document = env.upload(b"Not ready yet.")
        env.move(document["document_id"], env.folders[2])
    response = env.scoped(endpoint, {"folder_ids": [env.folders[2]]})
    assert document_ids(response, endpoint) == set()
    assert response.json()["data"]["reason_code"] == "no_ready_documents"
    if endpoint == "chat":
        assert response.json()["data"]["answer_status"] == "insufficient_evidence"
        with env.sessions() as db:
            run = db.get(QueryRun, uuid.UUID(response.json()["data"]["run_id"]))
            assert run.config_json["resolved_document_ids"] == []
    assert not env.embedding_calls and not env.provider.calls and not env.provider.counts


@pytest.mark.parametrize("endpoint", ["search", "chat"])
@pytest.mark.parametrize(
    "value",
    [None, "bad", ["bad"], [True], [str(uuid.uuid4())] * 2, [str(uuid.uuid4()) for _ in range(21)]],
)
def test_folder_filter_validation(folder_qa, endpoint, value):
    response = folder_qa.scoped(endpoint, {"folder_ids": value})
    assert response.status_code == 422, response.text
    assert not folder_qa.embedding_calls and not folder_qa.provider.calls


@pytest.mark.parametrize("endpoint", ["search", "chat"])
def test_explicit_document_validation_is_not_hidden_by_empty_intersection(folder_qa, endpoint):
    env = folder_qa
    pending = str(env.upload(b"Pending policy.")["document_id"])
    for ids, status in [([pending], 409), ([pending, str(uuid.uuid4())], 404)]:
        response = env.scoped(endpoint, {"folder_ids": [env.folders[2]], "document_ids": ids})
        assert response.status_code == status, response.text
    with env.sessions() as db:
        db.get(Document, uuid.UUID(pending)).status = "deleting"
        db.commit()
    response = env.scoped(endpoint, {"folder_ids": [env.folders[2]], "document_ids": [pending]})
    assert response.status_code == 410, response.text
    assert not env.embedding_calls and not env.provider.calls


@pytest.mark.parametrize("endpoint", ["search", "chat"])
def test_member_without_folder_filter_still_reads_unclassified_sources(folder_qa, endpoint):
    env = folder_qa
    doc = str(ready(env)["document_id"])
    with env.sessions() as db:
        db.get(User, env.user.id).role = "member"
        db.commit()
    for filters in ({}, {"folder_ids": []}):
        assert document_ids(env.scoped(endpoint, filters), endpoint) == {doc}


@pytest.mark.parametrize("endpoint", ["search", "chat"])
def test_twenty_distinct_folders_are_accepted(folder_qa, endpoint):
    env = folder_qa
    extra = [uuid.uuid4() for _ in range(17)]
    with env.sessions() as db:
        db.add_all(
            [
                Folder(
                    id=key,
                    workspace_id=env.user.workspace_id,
                    created_by=env.user.id,
                    name="Extra " + str(index),
                )
                for index, key in enumerate(extra)
            ]
        )
        db.commit()
    response = env.scoped(endpoint, {"folder_ids": env.folders + [str(key) for key in extra]})
    assert document_ids(response, endpoint) == set()
    assert response.json()["data"]["reason_code"] == "no_ready_documents"


def test_chat_folder_replay_normalization_conflict_and_resolved_snapshot(folder_qa):
    env = folder_qa
    first, second, empty = env.folders
    doc = str(ready(env)["document_id"])
    env.move(doc, first)
    response = env.ask(filters={"folder_ids": [second, first]})
    assert document_ids(response, "chat") == {doc}
    data = response.json()["data"]
    with env.sessions() as db:
        run = db.get(QueryRun, uuid.UUID(data["run_id"]))
        assert run.config_json["folder_ids"] == sorted([first, second])
        assert run.config_json["resolved_document_ids"] == [doc]
    calls, counts = len(env.provider.calls), len(env.provider.counts)
    env.move(doc, empty)
    # Replay retains the original query-time scope; a new request resolves again.
    replay = env.ask(filters={"folder_ids": [first, second]})
    assert document_ids(replay, "chat") == {doc}
    assert replay.json()["data"]["message_id"] == data["message_id"]
    assert len(env.provider.calls) == calls and len(env.provider.counts) == counts
    conflict = env.ask(filters={"folder_ids": [empty]})
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"
    assert document_ids(env.scoped("chat", {"folder_ids": [first, second]}), "chat") == set()
    with env.sessions() as db:
        assert db.get(QueryRun, uuid.UUID(data["run_id"])).config_json["resolved_document_ids"] == [
            doc
        ]


def test_empty_folder_filter_preserves_legacy_input_hash():
    payload = ChatQuery(session_id=uuid.uuid4(), client_request_id=uuid.uuid4(), question="policy")
    legacy = content_hash(
        {
            "session_id": str(payload.session_id),
            "question": payload.question,
            "mode": payload.retrieval_mode,
            "top_k": payload.top_k,
            "document_ids": [],
        }
    )
    assert input_hash(payload) == legacy
    assert (
        input_hash(
            payload.model_copy(
                update={
                    "filters": payload.filters.model_copy(update={"folder_ids": [uuid.uuid4()]})
                }
            )
        )
        != legacy
    )
