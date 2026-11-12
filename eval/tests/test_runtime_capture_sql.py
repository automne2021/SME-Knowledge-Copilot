"""Real SQL/Qdrant/auth/worker/chat capture; synthetic data and fake inference only."""

import asyncio
import io
import json
import subprocess
import threading
import uuid
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import create_engine, delete, select, text, update
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import UploadFile

from app.core.config import get_settings
from app.core.security import hash_password
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
    SourceBlock,
    User,
    Workspace,
)
from app.services.chunking import split_document
from app.services.embeddings import content_hash
from app.services.jobs import JobQueue
from app.services.parsing import PARSER_VERSION, parse_file
from app.services.uploads import register_upload, store_stream
from app.services.vectors import QdrantIndex
from app.worker import IngestionWorker
from eval.final_budget import RequestLedger, fingerprint
from eval.final_eval import freeze, read_json, run_replay, sha256, write_json
from eval.runtime_capture import CaptureRuntime, SqlCanonicalSources
from tests.database_safety import validate_test_database_url

ROOT = Path(__file__).resolve().parents[2]
POLICY = "Synthetic policy: reimbursement deadline is 30 days."


class Counter:
    def count(self, value):
        return len(value) + 4

    count_query = count


class Embedder:
    def encode(self, texts):
        return [[1.0] + [0.0] * 383 for _ in texts]

    def encode_query(self, value, deadline=None):
        return self.encode([value])[0]


@pytest.fixture(scope="module")
def capture_db():
    """Create/migrate only a derived local *_capture_test database, never dev."""
    from alembic import command
    from alembic.config import Config
    from psycopg import sql

    settings = get_settings()
    target = validate_test_database_url(settings.test_database_url, settings.database_url)
    name = target.database.removesuffix("_test") + "_capture_test"
    url = URL.create(
        "postgresql+psycopg",
        username=target.username,
        password=target.password,
        host=target.host,
        port=target.port,
        database=name,
    )
    validate_test_database_url(url.render_as_string(hide_password=False), settings.database_url)
    admin = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 5},
    )
    try:
        with admin.connect() as connection:
            exists = connection.scalar(
                text("select 1 from pg_database where datname=:name"), {"name": name}
            )
            if not exists:
                statement = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name))
                connection.exec_driver_sql(
                    statement.as_string(connection.connection.driver_connection)
                )
    finally:
        admin.dispose()
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    lock = engine.connect()
    assert lock.scalar(text("select pg_try_advisory_lock(10611, 1)")), (
        "Capture suite already running"
    )
    try:
        cfg = Config(str(ROOT / "backend/alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "backend/alembic"))
        with engine.begin() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
        with engine.connect() as connection:
            assert (
                connection.scalar(text("select version_num from alembic_version"))
                == "20261103_rag04"
            )
            assert (
                connection.scalar(
                    text(
                        "select count(*) from processing_jobs "
                        "where status in ('queued','retry_wait','running')"
                    )
                )
                == 0
            ), "Capture DB has pending work; do not claim another scope's jobs"
        yield engine
    finally:
        lock.execute(text("select pg_advisory_unlock(10611, 1)"))
        lock.close()
        engine.dispose()


@pytest.fixture(autouse=True)
def forbid_live_inference(monkeypatch):
    """No real provider/model construction; HTTP limited to testserver and local Qdrant."""
    from urllib.parse import urlsplit

    from app.services.embeddings import LocalEmbedder
    from app.services.gemini import GeminiProvider

    allowed = urlsplit(get_settings().qdrant_url)
    assert allowed.hostname in {"localhost", "127.0.0.1", "::1"}
    original = httpx.Client.send
    original_async = httpx.AsyncClient.send

    def check(request):
        url = request.url
        assert url.host == "testserver" or (
            url.scheme == allowed.scheme
            and url.host == allowed.hostname
            and url.port == (allowed.port or 80)
        ), "External HTTP prohibited in capture integration"

    def send(client, request, *args, **kwargs):
        check(request)
        return original(client, request, *args, **kwargs)

    async def send_async(client, request, *args, **kwargs):
        check(request)
        return await original_async(client, request, *args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError("Real inference construction prohibited")

    monkeypatch.setattr(httpx.Client, "send", send)
    monkeypatch.setattr(httpx.AsyncClient, "send", send_async)
    monkeypatch.setattr(GeminiProvider, "__init__", forbidden)
    monkeypatch.setattr(LocalEmbedder, "__init__", forbidden)
    original_open = Path.open

    def restricted_open(path, *args, **kwargs):
        resolved = path.resolve()
        if any(
            resolved.is_relative_to(ROOT / "eval" / folder)
            for folder in ("snapshots", "datasets", "seeds", "mappings", "reports")
        ):
            raise AssertionError("Integration uses synthetic corpus only")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", restricted_open)


@pytest.fixture(autouse=True)
def parser_child_packages(monkeypatch):
    # pgAdmin's embedded Python ignores PYTHONPATH. Keep the production parser
    # subprocess, timeout and serialization; bootstrap its import paths only.
    original = subprocess.run

    def run(args, **kwargs):
        if isinstance(args, list) and args[1:4] == ["-B", "-m", "app.services.parsing"]:
            paths = [str(ROOT / "backend"), str(ROOT / "backend/.venv/Lib/site-packages")]
            bootstrap = (
                "import sys,runpy; sys.path[:0]="
                + repr(paths)
                + "; sys.argv=['app.services.parsing']+sys.argv[1:]; "
                "runpy.run_module('app.services.parsing',run_name='__main__')"
            )
            args = [args[0], "-I", "-B", "-c", bootstrap, *args[4:]]
        return original(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)


@pytest.fixture
def sql_env(capture_db, tmp_path):
    from fastapi.testclient import TestClient

    from app.main import create_app

    sessions = sessionmaker(capture_db, expire_on_commit=False)
    user = SimpleNamespace(id=uuid.uuid4(), workspace_id=uuid.uuid4())
    data = tmp_path / "data"
    data.mkdir()
    source = data / "policy.txt"
    source.write_text(POLICY, encoding="utf-8")
    parsed = parse_file(source, "txt")
    chunks = split_document(parsed, Counter())
    assert len(chunks) == 1
    span = {
        "block_id": parsed.blocks[0].block_id,
        "char_start": 0,
        "char_end": len(POLICY),
        "role": "content",
    }
    gold = {
        "evidence_id": "gold-policy",
        "evidence_group_id": "deadline",
        "document_id": "policy",
        "quote": POLICY,
    }
    question = {
        "id": "synthetic-sql",
        "split": "dev",
        "family_id": "synthetic-sql",
        "question": "What is the synthetic reimbursement deadline?",
        "expected_answer": POLICY,
        "expected_abstain": False,
        "gold_evidence": [gold],
    }
    (data / "questions.jsonl").write_text(json.dumps(question) + "\n", encoding="utf-8")
    write_json(data / "source_blocks.json", [asdict(block) for block in parsed.blocks])
    (data / "human_review.csv").write_text(
        "question_id,annotator,reviewer,status\nsynthetic-sql,fixture-author,fixture-reviewer,approved\n",
        encoding="utf-8",
    )
    write_json(
        data / "corpus_manifest.json",
        {
            "label_status": "human_reviewed",  # Fixture contract only, never actual human review.
            "questions_sha256": sha256(data / "questions.jsonl"),
            "source_blocks_sha256": sha256(data / "source_blocks.json"),
            "human_review_sha256": sha256(data / "human_review.csv"),
            "documents": [{"path": "policy.txt", "sha256": sha256(source)}],
            "fixtures": [],
        },
    )
    mapping = {
        "parent_manifest_sha256": sha256(data / "corpus_manifest.json"),
        "parser_version": PARSER_VERSION,
        "documents": {
            "policy": {
                "sha256": sha256(source),
                "blocks": [asdict(block) for block in parsed.blocks],
                "chunks": [asdict(chunk) for chunk in chunks],
            }
        },
        "questions": [{"id": question["id"], "evidence": [gold | {"parser_spans": [span]}]}],
    }
    write_json(tmp_path / "mapping.json", mapping)
    index_version = content_hash({"synthetic_capture": True, "parser": PARSER_VERSION})
    write_json(
        tmp_path / "config.json",
        {
            "production_top_k": 5,
            "evaluation_top_k": 10,
            "expected_index_version": index_version,
        },
    )
    protocol_path = tmp_path / "protocol.json"
    protocol = freeze(tmp_path, "data", "mapping.json", "config.json", protocol_path)
    grant = {
        "scope_id": "sql-fixture-" + uuid.uuid4().hex,
        "protocol_sha256": fingerprint(protocol),
        "total": {"generateContent": 2, "countTokens": 7},
        "batches": {"synthetic": {"generateContent": 2, "countTokens": 7}},
    }
    ledger = RequestLedger.create(tmp_path / "ledger.sqlite", grant)
    scope = fingerprint(grant)[:16]
    settings = get_settings().model_copy(
        update={
            "storage_dir": tmp_path / "backend/.cache/final-capture" / scope,
            "qdrant_collection": "final_" + scope,
            "llm_api_key": None,
            "llm_free_tier_confirmed": False,
            "llm_quota_confirmed": False,
            "retrieval_score_threshold": None,
        }
    )
    embedding = {"synthetic_capture": True, "dimension": 384}
    profile = {
        "embedding_fingerprint": embedding,
        "embedding_hash": content_hash(embedding),
        "index_version": index_version,
        "parser_version": PARSER_VERSION,
        "chunking_config": {"fake_counter": True},
        "collection_name": settings.qdrant_collection,
    }
    vector = QdrantIndex(settings.qdrant_url, settings.qdrant_collection, 5)
    env = SimpleNamespace(
        root=tmp_path,
        sessions=sessions,
        user=user,
        settings=settings,
        vector=vector,
        ledger=ledger,
        protocol=protocol,
        protocol_path=protocol_path,
        counts=0,
        generations=0,
        before_generate=None,
    )
    with sessions() as db:
        db.add(Workspace(id=user.workspace_id, name="Synthetic capture integration"))
        db.flush()
        db.add(
            User(
                id=user.id,
                workspace_id=user.workspace_id,
                username="capture." + user.id.hex,
                email=user.id.hex + "@example.invalid",
                display_name="Capture fixture",
                role="knowledge_admin",
                password_hash=hash_password("fixture-password"),
            )
        )
        db.commit()
    try:
        vector.ensure_collection(profile["embedding_hash"])
        stored = asyncio.run(
            store_stream(
                UploadFile(io.BytesIO(POLICY.encode())),
                settings.storage_dir,
                user.workspace_id,
                "txt",
                20 * 1024**2,
            )
        )
        with sessions() as db:
            upload = register_upload(db, user, "policy.txt", "txt", stored)
        env.document_id = upload["document_id"]
        outcome = IngestionWorker(
            JobQueue(sessions, settings), vector, Embedder(), Counter(), profile
        ).run_once()
        assert outcome["job_id"] == str(upload["job_id"]) and outcome["status"] == "completed", (
            outcome
        )
        sources = SqlCanonicalSources(
            sessions, user.workspace_id, {"policy": env.document_id}, mapping, profile
        )

        class Provider:
            def count_tokens(self, payload, deadline):
                env.counts += 1
                return 100

            def generate(self, payload, deadline):
                env.generations += 1
                if env.before_generate:
                    env.before_generate()
                return {
                    "text": json.dumps(
                        {
                            "answer_status": "grounded",
                            "claims": [{"text": POLICY, "evidence_ids": ["E1"]}],
                            "limitations": [],
                            "missing_information": [],
                            "conflict_detected": False,
                        }
                    ),
                    "finish_reason": "STOP",
                    "usage": None,
                }

        spec = {
            "id": question["id"],
            "question": question["question"],
            "user_id": str(user.id),
            "workspace_id": str(user.workspace_id),
            "document_ids": [],
            "batch": "synthetic",
        }
        env.runtime = CaptureRuntime(
            tmp_path,
            protocol,
            "dev",
            [spec],
            ledger,
            sources,
            settings,
            lambda settings: Provider(),
        )
        search_runtime = SimpleNamespace(
            profile=profile,
            vector=vector,
            embedder=Embedder(),
            counter=Counter(),
            lock=threading.Lock(),
            close=lambda: None,
        )
        app = env.runtime.install(create_app(), search_runtime)
        env.app, env.sources = app, sources
        with TestClient(app) as client:
            env.client = client
            login = client.post(
                "/api/v1/auth/login",
                json={
                    "username": "capture." + user.id.hex,
                    "password": "fixture-password",
                },
            )
            assert login.status_code == 200
            env.auth = {"Authorization": "Bearer " + login.json()["data"]["access_token"]}
            session = client.post("/api/v1/chat/sessions", headers=env.auth, json={})
            assert session.status_code == 201
            env.payload = {
                "session_id": session.json()["data"]["id"],
                "question": question["question"],
                "client_request_id": str(uuid.uuid4()),
            }
            env.ask = lambda **kw: client.post(
                "/api/v1/chat/query", headers=env.auth, json=env.payload | kw
            )
            yield env
    finally:
        # Exact IDs/collection only. Keep synthetic filesystem artifacts for inspection.
        assert vector.collection == "final_" + scope
        vector._request("DELETE", allow_missing=True)
        vector.close()
        with sessions() as db:
            session_ids = select(ChatSession.id).where(
                ChatSession.workspace_id == user.workspace_id
            )
            messages = select(ChatMessage.id).where(ChatMessage.session_id.in_(session_ids))
            db.execute(delete(AnswerCitation).where(AnswerCitation.message_id.in_(messages)))
            db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(session_ids)))
            db.execute(delete(QueryRun).where(QueryRun.session_id.in_(session_ids)))
            db.execute(delete(ChatSession).where(ChatSession.id.in_(session_ids)))
            db.execute(delete(AuthToken).where(AuthToken.user_id == user.id))
            docs = select(Document.id).where(Document.workspace_id == user.workspace_id)
            revisions = select(DocumentRevision.id).where(DocumentRevision.document_id.in_(docs))
            db.execute(
                update(Document)
                .where(Document.workspace_id == user.workspace_id)
                .values(status="failed", active_revision_id=None, active_generation_id=None)
            )
            db.execute(delete(ProcessingJob).where(ProcessingJob.document_id.in_(docs)))
            db.execute(delete(Chunk).where(Chunk.revision_id.in_(revisions)))
            db.execute(delete(SourceBlock).where(SourceBlock.revision_id.in_(revisions)))
            db.execute(delete(DocumentRevision).where(DocumentRevision.document_id.in_(docs)))
            db.execute(delete(Document).where(Document.workspace_id == user.workspace_id))
            db.execute(delete(User).where(User.id == user.id))
            db.execute(delete(Workspace).where(Workspace.id == user.workspace_id))
            db.commit()


def test_sql_capture_publish_replay_export(sql_env):
    env = sql_env
    response = env.ask()
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["answer_status"] == "grounded" and len(result["citations"]) == 1
    assert env.generations == 1 and 1 <= env.counts <= 7
    before = env.ledger.snapshot()
    replay = env.ask()
    assert replay.status_code == 200 and replay.json()["data"] == result
    assert env.ledger.snapshot() == before and env.generations == 1
    assert env.ask(client_request_id=str(uuid.uuid4())).status_code == 409
    with env.sessions() as db:
        run = db.scalar(
            select(QueryRun).where(QueryRun.session_id == uuid.UUID(env.payload["session_id"]))
        )
        assert run.status == "completed"
        assert db.scalar(
            select(AnswerCitation).where(AnswerCitation.document_id == env.document_id)
        )
    output = env.root / "capture"
    env.runtime.export(output)
    capture = read_json(output / "capture.json")
    assert capture["origin"] == "offline_fixture"
    row = capture["rows"][0]
    assert row["status"] == "completed" and len(row["final_context"]) == 1
    assert row["retrieval"]["hits"][0]["document_id"] == "policy"
    run_replay(env.root, env.protocol_path, output / "capture.json", env.root / "report", "dev")
    human = read_json(env.root / "report/metrics.json")["human"]
    assert human["reviewed"] == 0 and human["pending_or_disputed"] == 1
    assert human["strict_success_rate"] is None
    execution = read_json(output / "execution.json")
    assert execution["auth_override_present"] is False
    assert execution["provider_kind"] == "fake"


def test_real_sql_budget_blocks_transport(sql_env):
    env = sql_env
    for _ in range(7):
        env.ledger.reserve("synthetic", "countTokens", "pre-exhaust-fixture")
    response = env.ask()
    assert response.status_code == 503, response.text
    assert response.json()["error"]["code"] == "eval_budget_exhausted"
    assert env.counts == env.generations == 0
    env.runtime.export(env.root / "failed-capture")
    row = read_json(env.root / "failed-capture/capture.json")["rows"][0]
    assert row["status"] == "failed" and row["retrieval"]["status"] == "completed"


def test_real_sql_source_change_during_generation_never_publishes(sql_env):
    env = sql_env

    def change():
        with env.sessions() as db:
            db.get(Document, env.document_id).status = "failed"
            db.commit()

    env.before_generate = change
    response = env.ask()
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "source_changed"
    assert env.generations == 1
    with env.sessions() as db:
        assert not db.scalar(
            select(AnswerCitation).where(AnswerCitation.document_id == env.document_id)
        )
        run = db.scalar(
            select(QueryRun).where(QueryRun.session_id == uuid.UUID(env.payload["session_id"]))
        )
        assert run.status == "failed"
    env.runtime.export(env.root / "changed-capture")
    row = read_json(env.root / "changed-capture/capture.json")["rows"][0]
    assert row["status"] == "failed" and row.get("answer") is None


def test_real_sql_canonical_drift_blocks_before_inference(sql_env):
    env = sql_env
    with env.sessions() as db:
        chunk = db.scalar(
            select(Chunk)
            .join(DocumentRevision)
            .where(DocumentRevision.document_id == env.document_id)
        )
        chunk.text = "Tampered canonical SQL text"
        db.commit()
    response = env.ask()
    assert response.status_code == 503, response.text
    assert response.json()["error"]["code"] == "eval_source_drift"
    assert env.counts == env.generations == 0
    env.runtime.export(env.root / "drift-capture")
    row = read_json(env.root / "drift-capture/capture.json")["rows"][0]
    assert row["status"] == "failed" and row.get("answer") is None


def test_capture_restricts_mutation_and_auth(sql_env):
    env = sql_env
    assert env.client.post("/api/v1/chat/query", json=env.payload).status_code == 401
    assert (
        env.client.delete("/api/v1/documents/" + str(env.document_id), headers=env.auth).status_code
        == 403
    )
    assert not env.runtime.attempts
    assert env.counts == env.generations == 0


def test_real_sql_no_ready_source_abstains_without_provider(sql_env):
    env = sql_env
    with env.sessions() as db:
        db.get(Document, env.document_id).status = "failed"
        db.commit()
    response = env.ask()
    assert response.status_code == 200, response.text
    assert response.json()["data"]["answer_status"] == "insufficient_evidence"
    assert env.counts == env.generations == 0
    env.runtime.export(env.root / "empty-capture")
    row = read_json(env.root / "empty-capture/capture.json")["rows"][0]
    assert row["status"] == "completed"
    assert row["retrieval"]["hits"] == row["final_context"] == []
