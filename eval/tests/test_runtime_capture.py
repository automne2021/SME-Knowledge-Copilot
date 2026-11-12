"""Real ASGI route/answering with explicitly stubbed identity, storage and retrieval.

No real SQL, embedding, model, browser or project holdout is used in this suite.
"""

import copy
import importlib
import json
import socket
import sqlite3
import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import AppError
from eval.final_budget import RequestLedger, fingerprint
from eval.final_eval import read_json, run_replay
from eval.runtime_capture import CaptureRuntime, SqlCanonicalSources
from eval.tests import test_final_eval as offline_fixtures

frozen = offline_fixtures.frozen
deny_network_and_project_corpus = offline_fixtures.deny_network_and_project_corpus
_CONNECT = socket.socket.connect


@pytest.fixture(autouse=True)
def asyncio_selfpipe_only(deny_network_and_project_corpus, monkeypatch):
    # Windows' asyncio creates a private socketpair using loopback. Allow only
    # that pair, not arbitrary loopback connections to DB/Qdrant/HTTP services.
    def pair(family=None, type=socket.SOCK_STREAM, proto=0):
        if type != socket.SOCK_STREAM or proto != 0:
            raise AssertionError("Unexpected socketpair type")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            _CONNECT(client, listener.getsockname())
            server, _ = listener.accept()
            return server, client
        except BaseException:
            client.close()
            raise
        finally:
            listener.close()

    monkeypatch.setattr(socket, "socketpair", pair)


@pytest.fixture
def api_env(frozen, monkeypatch):
    import app.core.config as config_module

    root, protocol_path, protocol, _, refs, _ = frozen
    settings = Settings(
        _env_file=None,
        database_url=("postgresql+psycopg://fixture:fixture@127.0.0.1/fixture_dev"),
        llm_api_key=None,
        llm_free_tier_confirmed=False,
        llm_quota_confirmed=False,
    )
    monkeypatch.setattr(config_module, "get_settings", lambda: settings)
    main_module = importlib.import_module("app.main")
    route_module = importlib.import_module("app.api.chat")
    chat_module = importlib.import_module("app.services.chat")
    from app.core.db import get_db
    from app.core.security import get_current_user

    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setattr(route_module, "get_settings", lambda: settings)
    state = SimpleNamespace(
        settings=settings,
        root=root,
        protocol=protocol,
        protocol_path=protocol_path,
        user=SimpleNamespace(id=uuid.uuid4(), workspace_id=uuid.uuid4()),
        cached={},
        runs={},
        counts=0,
        generations=0,
        reply="valid",
        fail_source=False,
        empty=False,
        two_hits=False,
        failed_runs=[],
    )
    hits = [
        {
            "chunk_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "revision_id": str(uuid.uuid4()),
            "generation_id": str(uuid.uuid4()),
            "excerpt": "abcdefghij",
            "source": {"file_name": f"fixture-{index}.txt"},
        }
        for index in range(2)
    ]

    class Sources:
        def references(self, items):
            if state.fail_source:
                raise ValueError("fixture source drift")
            result = []
            for item in items:
                matches = [
                    index
                    for index, hit in enumerate(hits)
                    if all(
                        item[key] == hit[key]
                        for key in (
                            "chunk_id",
                            "document_id",
                            "revision_id",
                            "generation_id",
                            "excerpt",
                        )
                    )
                ]
                if len(matches) != 1:
                    raise ValueError("forged fixture source")
                result.append(copy.deepcopy(refs[matches[0]]))
            return result

    class Provider:
        def count_tokens(self, payload, deadline):
            state.counts += 1
            return 100

        def generate(self, payload, deadline):
            state.generations += 1
            state.last_payload = copy.deepcopy(payload)
            if state.reply == "timeout":
                raise AppError(504, "model_timeout", "Fixture provider timeout")
            answer = {
                "answer_status": "grounded",
                "claims": [
                    {
                        "text": "abcdefghij",
                        "evidence_ids": [
                            "E99" if state.reply == "repair" and state.generations == 1 else "E1"
                        ],
                    }
                ],
                "limitations": [],
                "missing_information": [],
                "conflict_detected": False,
            }
            return {"text": json.dumps(answer), "finish_reason": "STOP", "usage": None}

    class Db:
        def commit(self):
            pass

        def scalar(self, statement):
            return state.current_run

        def execute(self, statement):
            return SimpleNamespace(rowcount=1)

    def start(db, user, payload, runtime_settings):
        identity = str(payload.client_request_id)
        run = state.runs.setdefault(identity, SimpleNamespace(id=uuid.uuid4(), status="running"))
        state.current_run = run
        return run, state.cached.get(identity)

    def search(*args, **kwargs):
        selected = [] if state.empty else copy.deepcopy(hits[: 2 if state.two_hits else 1])
        return {
            "hits": selected,
            "trace": {},
            "timings_ms": {"total": 3.0},
            "reason_code": "no_ready_documents" if state.empty else None,
        }

    def publish(db, user, run_id, evidence, answer, trace, reason, timings, deadline):
        result = answer.model_dump() | {"run_id": str(run_id), "timings_ms": timings}
        for identity, run in state.runs.items():
            if run.id == run_id:
                state.cached[identity] = result
        return result

    monkeypatch.setattr(chat_module, "start_run", start)
    monkeypatch.setattr(chat_module, "search", search)
    monkeypatch.setattr(chat_module, "source_state", lambda db, user, evidence, **kw: evidence)
    monkeypatch.setattr(chat_module, "publish", publish)
    monkeypatch.setattr(
        chat_module,
        "fail_run",
        lambda db, run_id, error: state.failed_runs.append((str(run_id), error.code)),
    )
    state.app = main_module.create_app()
    state.app.dependency_overrides[get_db] = lambda: Db()
    state.app.dependency_overrides[get_current_user] = lambda: state.user
    state.get_current_user = get_current_user
    state.sources, state.provider = Sources(), Provider()
    state.spec = {
        "id": "fixture-1",
        "question": "Synthetic fixture only",
        "user_id": str(state.user.id),
        "workspace_id": str(state.user.workspace_id),
        "document_ids": [],
        "batch": "main",
    }
    state.payload = {
        "session_id": str(uuid.uuid4()),
        "client_request_id": str(uuid.uuid4()),
        "question": state.spec["question"],
        "retrieval_mode": "dense",
        "top_k": 5,
    }

    def install(generation=2, counting=7):
        allowance = {
            "scope_id": "fixture-api",
            "protocol_sha256": fingerprint(protocol),
            "total": {"generateContent": generation, "countTokens": counting},
            "batches": {"main": {"generateContent": generation, "countTokens": counting}},
        }
        ledger = RequestLedger.create(root / "runtime.sqlite", allowance)
        runtime = CaptureRuntime(
            root,
            protocol,
            "dev",
            [state.spec],
            ledger,
            state.sources,
            settings,
            lambda cfg: state.provider,
        )
        runtime.install(state.app)
        state.runtime, state.ledger = runtime, ledger
        return runtime

    state.install = install
    return state


def test_real_route_context_builder_and_capture_replay_round_trip(api_env):
    env = api_env
    env.two_hits = True
    runtime = env.install()
    with TestClient(env.app) as client:
        result = client.post("/api/v1/chat/query", json=env.payload)
    assert result.status_code == 200 and result.json()["data"]["answer_status"] == "grounded"
    assert env.counts == 4 and env.generations == 1
    captured = runtime.export(env.root / "exported")
    assert captured["origin"] == "offline_fixture"
    row = captured["rows"][0]
    assert len(row["final_context"]) == 2  # Includes uncited evidence, not just citations.
    assert row["answer"]["claims"][0]["evidence_ids"] == ["E1"]
    execution = read_json(env.root / "exported/execution.json")
    assert execution["ledger"]["total"] == {"generateContent": 1, "countTokens": 4}
    assert execution["provider_kind"] == "fake" and execution["auth_override_present"]
    manifest = run_replay(
        env.root,
        env.protocol_path,
        env.root / "exported/capture.json",
        env.root / "replayed",
        "dev",
    )
    assert manifest["origin"] == "offline_fixture" and manifest["human_review"] == "pending"


def test_budget_failure_is_typed_and_never_sends_unreserved_request(api_env):
    env = api_env
    runtime = env.install(counting=2)
    with TestClient(env.app) as client:
        response = client.post("/api/v1/chat/query", json=env.payload)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "eval_budget_exhausted"
    assert env.counts == 2 and env.generations == 0
    assert env.failed_runs[-1][1] == "eval_budget_exhausted"
    row = runtime.export(env.root / "exported")["rows"][0]
    assert row["status"] == "failed" and row["error"] == "budget"
    assert "answer" not in row and row["retrieval"]["status"] == "completed"


def test_ledger_loss_blocks_factory_transport_and_preserves_typed_error(api_env):
    env = api_env
    env.install()
    env.ledger.path.unlink()
    with TestClient(env.app) as client:
        result = client.post("/api/v1/chat/query", json=env.payload)
    assert result.status_code == 503 and result.json()["error"]["code"] == "eval_ledger_unavailable"
    assert env.counts == env.generations == 0
    with pytest.raises(sqlite3.OperationalError):
        env.runtime.export(env.root / "incomplete-export")
    assert not (env.root / "incomplete-export").exists()


def test_idempotent_replay_does_not_overwrite_capture_or_spend_again(api_env):
    env = api_env
    runtime = env.install()
    with TestClient(env.app) as client:
        first = client.post("/api/v1/chat/query", json=env.payload)
        second = client.post("/api/v1/chat/query", json=env.payload)
        third = client.post(
            "/api/v1/chat/query", json={**env.payload, "client_request_id": str(uuid.uuid4())}
        )
    assert first.status_code == second.status_code == 200
    assert first.json()["data"] == second.json()["data"]
    assert third.status_code == 409
    assert env.counts == 3 and env.generations == 1 and len(runtime.attempts) == 1


@pytest.mark.parametrize("change", ["question", "top_k", "filters", "workspace"])
def test_unapproved_query_never_reaches_pipeline_or_provider(api_env, change):
    env = api_env
    env.install()
    payload = copy.deepcopy(env.payload)
    if change == "question":
        payload["question"] = "Unapproved question"
    elif change == "top_k":
        payload["top_k"] = 10
    elif change == "filters":
        payload["filters"] = {"document_ids": [str(uuid.uuid4())]}
    else:
        env.user.workspace_id = uuid.uuid4()
    with TestClient(env.app) as client:
        result = client.post("/api/v1/chat/query", json=payload)
    assert result.status_code == 403 and env.counts == env.generations == 0
    assert not env.runs


def test_source_drift_stops_before_counting_and_is_not_abstention(api_env):
    env = api_env
    runtime = env.install()
    env.fail_source = True
    with TestClient(env.app) as client:
        result = client.post("/api/v1/chat/query", json=env.payload)
    assert result.status_code == 503 and result.json()["error"]["code"] == "eval_source_drift"
    assert env.counts == env.generations == 0
    assert runtime.export(env.root / "exported")["rows"][0]["error"] == "retrieval"


def test_repair_is_reserved_as_second_generation_and_unknown_usage_stays_null(api_env):
    env = api_env
    env.reply = "repair"
    runtime = env.install()
    with TestClient(env.app) as client:
        result = client.post("/api/v1/chat/query", json=env.payload)
    assert result.status_code == 200 and env.generations == 2
    assert env.ledger.snapshot()["total"]["generateContent"] == 2
    assert [call["usage"] for call in runtime.attempts["fixture-1"].calls] == [None] * 5


def test_provider_timeout_is_not_misclassified_as_ledger_failure(api_env):
    env = api_env
    env.reply = "timeout"
    runtime = env.install()
    with TestClient(env.app) as client:
        result = client.post("/api/v1/chat/query", json=env.payload)
    assert result.status_code == 504 and env.generations == 1
    assert env.ledger.snapshot()["total"]["generateContent"] == 1
    assert runtime.export(env.root / "exported")["rows"][0]["error"] == "timeout"


def test_no_hits_abstains_without_provider_calls(api_env):
    env = api_env
    env.empty = True
    runtime = env.install()
    with TestClient(env.app) as client:
        result = client.post("/api/v1/chat/query", json=env.payload)
    assert result.status_code == 200
    row = runtime.export(env.root / "exported")["rows"][0]
    assert row["answer"]["answer_status"] == "insufficient_evidence"
    assert row["final_context"] == [] and env.counts == env.generations == 0


def test_config_drift_is_blocked_before_first_provider_call(api_env):
    env = api_env
    env.install()
    env.app.state.rag_settings.llm_max_output_tokens = 900
    with TestClient(env.app) as client:
        result = client.post("/api/v1/chat/query", json=env.payload)
    assert result.status_code == 503 and result.json()["error"]["code"] == "eval_config_drift"
    assert env.counts == env.generations == 0


def test_runtime_binding_survives_restart_and_rejects_plan_changes(api_env):
    env = api_env
    env.install()
    specs = [{**env.spec, "document_ids": [str(uuid.uuid4())]}]
    with pytest.raises(ValueError, match="Runtime plan differs"):
        CaptureRuntime(
            env.root,
            env.protocol,
            "dev",
            specs,
            env.ledger,
            env.sources,
            env.settings,
            lambda cfg: env.provider,
        )
    with pytest.raises(ValueError, match="explicit authorization"):
        from app.services.gemini import GeminiProvider

        CaptureRuntime(
            env.root,
            env.protocol,
            "dev",
            [env.spec],
            env.ledger,
            env.sources,
            env.settings,
            GeminiProvider,
            provider_kind="native_gemini",
        )


def test_auth_dependency_runs_before_scope_and_default_app_still_works(api_env):
    env = api_env
    env.install()
    del env.app.dependency_overrides[env.get_current_user]
    with TestClient(env.app) as client:
        result = client.post("/api/v1/chat/query", json=env.payload)
    assert result.status_code == 401 and not env.runs and env.counts == 0


def test_capture_disabled_route_keeps_original_behavior(api_env):
    env = api_env
    env.app.state.provider_factory = lambda settings: env.provider
    with TestClient(env.app) as client:
        result = client.post("/api/v1/chat/query", json=env.payload)
    assert result.status_code == 200 and env.counts == 3 and env.generations == 1


def test_scoped_app_blocks_document_mutations_and_unguarded_factory(api_env):
    env = api_env
    runtime = env.install()
    with TestClient(env.app) as client:
        upload = client.post("/api/v1/documents")
        delete = client.delete("/api/v1/documents/" + str(uuid.uuid4()))
    assert upload.status_code == delete.status_code == 403
    with pytest.raises(AppError) as exc:
        runtime.reject_uncaptured(env.settings)
    assert exc.value.code == "eval_scope_required" and env.counts == env.generations == 0


def test_plan_mutation_is_rejected_before_query_or_export(api_env):
    env = api_env
    runtime = env.install()
    runtime.specs["fixture-1"]["batch"] = "unapproved-batch"
    with TestClient(env.app) as client:
        response = client.post("/api/v1/chat/query", json=env.payload)
    assert response.status_code == 503 and response.json()["error"]["code"] == "eval_plan_drift"
    assert env.counts == env.generations == 0
    with pytest.raises(ValueError, match="changed"):
        runtime.export(env.root / "exported")


def test_source_content_uses_scoped_settings_instead_of_global_profile(api_env, monkeypatch):
    env = api_env
    env.install()
    import app.api.search as route

    env.app.state.rag_settings.storage_dir = env.root / "isolated-source-storage"
    seen = []

    def content(db, user, document_id, settings):
        seen.append(settings.storage_dir)
        return b"fixture-only", "text/plain", {}

    monkeypatch.setattr(route, "source_content", content)
    with TestClient(env.app) as client:
        response = client.get(f"/api/v1/documents/{uuid.uuid4()}/content")
    assert response.status_code == 200 and response.content == b"fixture-only"
    assert seen == [env.app.state.rag_settings.storage_dir]


def test_sql_runtime_rejects_dev_db_and_requires_isolated_collection_storage(api_env):
    env = api_env
    env.install()
    from sqlalchemy.engine import make_url

    def sessions():
        raise AssertionError("SQL connections must not happen in target validation")

    sessions.kw = {"bind": SimpleNamespace(url=make_url(env.settings.database_url))}
    mapping = read_json(env.root / "mapping.json")
    sources = SqlCanonicalSources(
        sessions,
        env.user.workspace_id,
        {key: uuid.uuid4() for key in mapping["documents"]},
        mapping,
        {},
    )
    with pytest.raises(RuntimeError, match="differ from development"):
        CaptureRuntime(
            env.root,
            env.protocol,
            "dev",
            [env.spec],
            env.ledger,
            sources,
            env.settings,
            lambda cfg: env.provider,
        )
    sessions.kw["bind"].url = make_url(
        "postgresql+psycopg://fixture:fixture@127.0.0.1:5433/fixture_runtime_test"
    )
    with pytest.raises(ValueError, match="own collection"):
        CaptureRuntime(
            env.root,
            env.protocol,
            "dev",
            [env.spec],
            env.ledger,
            sources,
            env.settings,
            lambda cfg: env.provider,
        )


def test_sql_scope_install_requires_matching_runtime_and_overrides_db(api_env):
    env = api_env
    from sqlalchemy.engine import make_url

    from app.core.db import get_db

    allowance = {
        "scope_id": "fixture-sql",
        "protocol_sha256": fingerprint(env.protocol),
        "total": {"generateContent": 2, "countTokens": 7},
        "batches": {"main": {"generateContent": 2, "countTokens": 7}},
    }
    ledger = RequestLedger.create(env.root / "sql-scope.sqlite", allowance)
    scope = fingerprint(allowance)[:16]
    settings = env.settings.model_copy(
        update={
            "qdrant_collection": "final_" + scope,
            "storage_dir": env.root / "backend/.cache/final-capture" / scope,
        }
    )

    def sessions():
        raise AssertionError("SQL sessions are not invoked by install")

    sessions.kw = {
        "bind": SimpleNamespace(
            url=make_url("postgresql+psycopg://fixture:fixture@127.0.0.1:5433/fixture_runtime_test")
        )
    }
    mapping = read_json(env.root / "mapping.json")
    sources = SqlCanonicalSources(
        sessions,
        env.user.workspace_id,
        {key: uuid.uuid4() for key in mapping["documents"]},
        mapping,
        {"collection_name": settings.qdrant_collection, "index_version": None},
    )
    runtime = CaptureRuntime(
        env.root,
        env.protocol,
        "dev",
        [env.spec],
        ledger,
        sources,
        settings,
        lambda cfg: env.provider,
    )
    assert runtime.origin == "offline_fixture"  # SQL + fake generation is not a real-model run.
    with pytest.raises(ValueError, match="matching search runtime"):
        runtime.install(env.app)
    original_db = env.app.dependency_overrides[get_db]
    runtime.install(env.app, SimpleNamespace(profile=sources.profile, close=lambda: None))
    assert env.app.dependency_overrides[get_db] is not original_db
    assert env.app.state.rag_settings.storage_dir == settings.storage_dir


def test_sql_source_adapter_uses_active_mapping_and_rejects_foreign_ids(api_env, monkeypatch):
    env = api_env
    import eval.retrieval_gold as gold
    from app.models import Document

    document_id, revision_id, generation_id, chunk_id = [uuid.uuid4() for _ in range(4)]
    document = SimpleNamespace(active_revision_id=revision_id, active_generation_id=generation_id)
    chunk = SimpleNamespace(
        id=chunk_id,
        revision_id=revision_id,
        generation_id=generation_id,
        text_sha256="fixture-hash",
    )

    class Db:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, model, identity):
            assert model is Document and identity == document_id
            return document

        def scalars(self, statement):
            return SimpleNamespace(all=lambda: [chunk])

    called = []

    def loader(db, workspace, uploaded, mapping, profile):
        assert workspace == env.user.workspace_id and uploaded == {"doc1": document_id}
        called.append(True)
        return {"chunk_text": {str(chunk_id): "abcdefghij"}}

    monkeypatch.setattr(gold, "load_active_mapping", loader)
    sources = SqlCanonicalSources(
        Db, env.user.workspace_id, {"doc1": document_id}, {"documents": {"doc1": {}}}, {}
    )
    hit = {
        "chunk_id": str(chunk_id),
        "document_id": str(document_id),
        "revision_id": str(revision_id),
        "generation_id": str(generation_id),
        "excerpt": "abcdefghij",
    }
    assert sources.references([hit])[0]["document_id"] == "doc1" and called
    with pytest.raises(ValueError, match="outside"):
        sources.references([{**hit, "document_id": str(uuid.uuid4())}])
    with pytest.raises(ValueError, match="differs"):
        sources.references([{**hit, "excerpt": "forged"}])
    assert sources.references([]) == []
