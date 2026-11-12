"""One approved two-question native smoke; immutable scope, no retries/downloads."""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import secrets
import subprocess
import threading
import uuid
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlsplit

import httpx
from sqlalchemy import case, create_engine, delete, select, text, update
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import UploadFile

from app.core.config import Settings
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
from app.services.chunking import E5TokenCounter
from app.services.embeddings import LocalEmbedder, frozen_profile
from app.services.gemini import GeminiProvider
from app.services.ingestion import prepare_document
from app.services.jobs import JobQueue
from app.services.uploads import register_upload, store_stream
from app.services.vectors import QdrantIndex
from app.worker import IngestionWorker
from eval.final_budget import RequestLedger, fingerprint
from eval.final_eval import freeze, run_replay, sha256, write_json
from eval.runtime_capture import CaptureRuntime, SqlCanonicalSources
from tests.database_safety import validate_test_database_url

ROOT = Path(__file__).resolve().parents[1]
SCOPE_ID = "native-dev-smoke-20261110"
CAPS = {"generateContent": 4, "countTokens": 14}
POLICY = (
    "DỮ LIỆU TỔNG HỢP — QUY ĐỊNH CÔNG TÁC PHÍ. "
    "Nhân viên phải nộp đề nghị hoàn ứng trong vòng 30 ngày kể từ ngày kết thúc chuyến công tác. "
    "Hồ sơ gồm hóa đơn và xác nhận của quản lý. "
    "Tài liệu này không quy định chính sách nghỉ phép hoặc trợ cấp làm việc từ xa."
)
QUOTE = (
    "Nhân viên phải nộp đề nghị hoàn ứng trong vòng 30 ngày kể từ ngày kết thúc chuyến công tác. "
    "Hồ sơ gồm hóa đơn và xác nhận của quản lý."
)
QUESTIONS = (
    (
        "smoke-answerable",
        "Nhân viên phải nộp đề nghị hoàn ứng trong thời hạn nào và cần những hồ sơ gì?",
        False,
    ),
    (
        "smoke-unanswerable",
        "Theo chính sách công ty, mỗi nhân viên có bao nhiêu ngày nghỉ phép năm?",
        True,
    ),
)


def preflight(settings):
    # Constructor checks manual confirmations only, never sends HTTP.
    GeminiProvider(settings)
    target = validate_test_database_url(settings.test_database_url, settings.database_url)
    url = URL.create(
        "postgresql+psycopg",
        username=target.username,
        password=target.password,
        host=target.host,
        port=target.port,
        database=target.database.removesuffix("_test") + "_smoke_test",
    )
    validate_test_database_url(url.render_as_string(hide_password=False), settings.database_url)
    if urlsplit(settings.qdrant_url).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Smoke requires local Qdrant")
    profile = frozen_profile(settings)  # local_files_only=True; no inference/download.
    return url, profile


@contextmanager
def parser_packages(root):
    """Preserve the real parser child on pgAdmin embedded Python (_pth mode)."""
    original = subprocess.run

    def run(args, **kwargs):
        if isinstance(args, list) and args[1:4] == ["-B", "-m", "app.services.parsing"]:
            paths = [str(root / "backend"), str(root / "backend/.venv/Lib/site-packages")]
            boot = (
                "import sys,runpy;sys.path[:0]="
                + repr(paths)
                + ";sys.argv=['app.services.parsing']+sys.argv[1:];"
                "runpy.run_module('app.services.parsing',run_name='__main__')"
            )
            args = [args[0], "-I", "-B", "-c", boot, *args[4:]]
        return original(args, **kwargs)

    with patch("subprocess.run", run):
        yield


def prepare_inputs(
    root,
    output,
    settings,
    profile,
    counter,
    *,
    question_plan=None,
    scope_id=SCOPE_ID,
    caps=None,
    synthetic_e2e=False,
):
    question_plan = QUESTIONS if question_plan is None else question_plan
    caps = CAPS if caps is None else caps
    data = output / "data"
    data.mkdir()
    source = data / "policy.txt"
    source.write_text(POLICY, encoding="utf-8")
    with parser_packages(root):
        parsed, chunks = prepare_document(source, "txt", settings, counter)
    block = next(block for block in parsed.blocks if QUOTE in block.normalized_text)
    start = block.normalized_text.index(QUOTE)
    span = {
        "block_id": block.block_id,
        "char_start": start,
        "char_end": start + len(QUOTE),
        "role": "content",
    }
    gold = {
        "evidence_id": "gold-deadline",
        "evidence_group_id": "deadline",
        "document_id": "policy",
        "quote": QUOTE,
    }
    rows, mapped = [], []
    for identity, question, abstain in question_plan:
        evidence = [] if abstain else [gold]
        rows.append(
            {
                "id": identity,
                "split": "dev",
                "family_id": identity,
                "question": question,
                "expected_answer": "" if abstain else QUOTE,
                "expected_abstain": abstain,
                "gold_evidence": evidence,
            }
        )
        mapped.append(
            {"id": identity, "evidence": [] if abstain else [gold | {"parser_spans": [span]}]}
        )
    (data / "questions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    write_json(data / "source_blocks.json", [asdict(block) for block in parsed.blocks])
    (data / "human_review.csv").write_text(
        "question_id,annotator,reviewer,status\n"
        + "".join(row["id"] + ",,,synthetic_fixture\n" for row in rows),
        encoding="utf-8",
    )
    write_json(
        data / "corpus_manifest.json",
        {
            "label_status": "synthetic_browser_e2e" if synthetic_e2e else "synthetic_smoke",
            "questions_sha256": sha256(data / "questions.jsonl"),
            "source_blocks_sha256": sha256(data / "source_blocks.json"),
            "human_review_sha256": sha256(data / "human_review.csv"),
            "documents": [{"path": "policy.txt", "sha256": sha256(source)}],
            "fixtures": [],
        },
    )
    mapping = {
        "parent_manifest_sha256": sha256(data / "corpus_manifest.json"),
        "parser_version": parsed.parser_version,
        "documents": {
            "policy": {
                "sha256": sha256(source),
                "blocks": [asdict(block) for block in parsed.blocks],
                "chunks": [asdict(chunk) for chunk in chunks],
            }
        },
        "questions": mapped,
    }
    write_json(output / "mapping.json", mapping)
    config = {
        "production_top_k": settings.retrieval_top_k,
        "evaluation_top_k": 10,
        "expected_index_version": profile["index_version"],
        "candidate_k": settings.retrieval_candidate_k,
        "score_threshold": settings.retrieval_score_threshold,
        "model": settings.embedding_model,
        "revision": settings.embedding_revision,
        "dimension": settings.embedding_dimension,
        "chunk_size_tokens": settings.chunk_size_tokens,
        "chunk_overlap_tokens": settings.chunk_overlap_tokens,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "llm_evidence_budget_tokens": settings.llm_evidence_budget_tokens,
        "llm_max_output_tokens": settings.llm_max_output_tokens,
        "llm_safety_margin_tokens": settings.llm_safety_margin_tokens,
        "llm_context_window_tokens": settings.llm_context_window_tokens,
        "llm_call_timeout_seconds": settings.llm_call_timeout_seconds,
        "query_timeout_seconds": settings.query_timeout_seconds,
        "request_caps": caps,
        "human_labels": "not_reviewed_synthetic_smoke_only",
    }
    write_json(output / "config.json", config)
    sources = sorted(
        path.relative_to(root).as_posix()
        for path in [*(root / "backend/app").rglob("*.py"), *(root / "eval").glob("*.py")]
    )
    protocol = freeze(
        root,
        data.relative_to(root),
        (output / "mapping.json").relative_to(root),
        (output / "config.json").relative_to(root),
        output / "protocol.json",
        sources,
        synthetic_smoke=not synthetic_e2e,
        synthetic_e2e=synthetic_e2e,
    )
    grant = {
        "scope_id": scope_id,
        "protocol_sha256": fingerprint(protocol),
        "total": caps,
        "batches": {
            identity: {"generateContent": 0, "countTokens": 0}
            if identity.endswith("after-delete")
            else {"generateContent": 2, "countTokens": 7}
            for identity, _, _ in question_plan
        },
    }
    write_json(output / "grant.json", grant)
    ledger = RequestLedger.create(output / "requests.sqlite", grant)
    return rows, mapping, protocol, ledger


@contextmanager
def database(url):
    from alembic import command
    from alembic.config import Config
    from psycopg import sql

    admin = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 5},
    )
    try:
        with admin.connect() as connection:
            exists = connection.scalar(
                text("select 1 from pg_database where datname=:name"), {"name": url.database}
            )
            if not exists:
                command_sql = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(url.database))
                connection.exec_driver_sql(
                    command_sql.as_string(connection.connection.driver_connection)
                )
    finally:
        admin.dispose()
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    try:
        with engine.connect() as lock:
            if not lock.scalar(text("select pg_try_advisory_lock(10611,2)")):
                raise RuntimeError("Another smoke owns this database")
            try:
                cfg = Config(str(ROOT / "backend/alembic.ini"))
                cfg.set_main_option("script_location", str(ROOT / "backend/alembic"))
                with engine.begin() as connection:
                    cfg.attributes["connection"] = connection
                    command.upgrade(cfg, "head")
                with engine.connect() as connection:
                    if connection.scalar(
                        text(
                            "select count(*) from processing_jobs "
                            "where status in ('queued','retry_wait','running')"
                        )
                    ):
                        raise RuntimeError("Smoke database has pending work")
                yield sessionmaker(engine, expire_on_commit=False)
            finally:
                lock.execute(text("select pg_advisory_unlock(10611,2)"))
    finally:
        engine.dispose()


def cleanup(sessions, vector, settings, workspace_id, user_id, storage_keys, *, extra_user_ids=()):
    """Delete only owned scope; preserve SQL schema and report/ledger files."""
    if not settings.qdrant_collection.startswith("final_"):
        raise ValueError("Invalid cleanup collection")
    vector._request("DELETE", allow_missing=True)
    if vector._request("GET", allow_missing=True) is not None:
        raise RuntimeError("Smoke collection still exists")
    with sessions() as db:
        spaces = select(ChatSession.id).where(ChatSession.workspace_id == workspace_id)
        messages = select(ChatMessage.id).where(ChatMessage.session_id.in_(spaces))
        db.execute(delete(AnswerCitation).where(AnswerCitation.message_id.in_(messages)))
        db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(spaces)))
        db.execute(delete(QueryRun).where(QueryRun.session_id.in_(spaces)))
        db.execute(delete(ChatSession).where(ChatSession.id.in_(spaces)))
        user_ids = [user_id, *extra_user_ids]
        db.execute(delete(AuthToken).where(AuthToken.user_id.in_(user_ids)))
        docs = select(Document.id).where(Document.workspace_id == workspace_id)
        revisions = select(DocumentRevision.id).where(DocumentRevision.document_id.in_(docs))
        db.execute(
            update(Document)
            .where(Document.workspace_id == workspace_id)
            .values(
                status=case((Document.status == "deleted", "deleted"), else_="failed"),
                active_revision_id=None,
                active_generation_id=None,
            )
        )
        db.execute(delete(ProcessingJob).where(ProcessingJob.document_id.in_(docs)))
        db.execute(delete(Chunk).where(Chunk.revision_id.in_(revisions)))
        db.execute(delete(SourceBlock).where(SourceBlock.revision_id.in_(revisions)))
        db.execute(delete(DocumentRevision).where(DocumentRevision.document_id.in_(docs)))
        db.execute(delete(Document).where(Document.workspace_id == workspace_id))
        db.execute(delete(User).where(User.id.in_(user_ids), User.workspace_id == workspace_id))
        db.execute(delete(Workspace).where(Workspace.id == workspace_id))
        db.commit()
        if db.get(Workspace, workspace_id) is not None:
            raise RuntimeError("Smoke workspace still exists")
    root = settings.storage_dir.resolve()
    for key in storage_keys:
        path = (root / key).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Cleanup path escapes smoke storage")
        path.unlink(missing_ok=True)


@contextmanager
def native_http_events(summary):
    """Observe status only, without extra requests or retaining credentials/raw bodies."""
    from app.services.gemini import BASE_URL, MODEL

    original = httpx.AsyncClient.send
    events = summary.setdefault("native_http_events", [])

    async def send(client, request, *args, **kwargs):
        actions = {
            BASE_URL + "/models/" + MODEL + ":" + action: action
            for action in ("generateContent", "countTokens")
        }
        action = actions.get(str(request.url))
        if action is None:
            return await original(client, request, *args, **kwargs)
        event = {"action": action, "http_status": None}
        events.append(event)
        try:
            response = await original(client, request, *args, **kwargs)
        except Exception as exc:
            event["error_type"] = type(exc).__name__
            raise
        event["http_status"] = response.status_code
        return response

    with patch("httpx.AsyncClient.send", send):
        yield


def capture(
    sessions, settings, profile, counter, embedder, output, rows, mapping, protocol, ledger, summary
):
    from fastapi.testclient import TestClient

    from app.main import create_app

    user = SimpleNamespace(id=uuid.uuid4(), workspace_id=uuid.uuid4())
    password = secrets.token_urlsafe(24)
    username = "native-smoke." + user.id.hex
    vector = QdrantIndex(
        settings.qdrant_url, settings.qdrant_collection, settings.vector_timeout_seconds
    )
    keys = []
    runtime = None
    try:
        with sessions() as db:
            db.add(Workspace(id=user.workspace_id, name="Native synthetic smoke only"))
            db.flush()
            db.add(
                User(
                    id=user.id,
                    workspace_id=user.workspace_id,
                    username=username,
                    email=user.id.hex + "@example.invalid",
                    display_name="Smoke fixture",
                    role="knowledge_admin",
                    password_hash=hash_password(password),
                )
            )
            db.commit()
        vector.ensure_collection(profile["embedding_hash"])
        stored = asyncio.run(
            store_stream(
                UploadFile(io.BytesIO(POLICY.encode())),
                settings.storage_dir,
                user.workspace_id,
                "txt",
                settings.max_upload_mb * 1024**2,
            )
        )
        keys.append(stored.storage_key)
        with sessions() as db:
            upload = register_upload(db, user, "synthetic-policy.txt", "txt", stored)
        with parser_packages(ROOT):
            result = IngestionWorker(
                JobQueue(sessions, settings), vector, embedder, counter, profile
            ).run_once()
        summary["ingestion"] = result
        if (
            not result
            or result["job_id"] != str(upload["job_id"])
            or result["status"] != "completed"
        ):
            raise RuntimeError("Synthetic ingestion failed")
        source = SqlCanonicalSources(
            sessions, user.workspace_id, {"policy": upload["document_id"]}, mapping, profile
        )
        specs = [
            {
                "id": row["id"],
                "question": row["question"],
                "user_id": str(user.id),
                "workspace_id": str(user.workspace_id),
                "document_ids": [],
                "batch": row["id"],
            }
            for row in rows
        ]
        runtime = CaptureRuntime(
            ROOT,
            protocol,
            "dev",
            specs,
            ledger,
            source,
            settings,
            GeminiProvider,
            provider_kind="native_gemini",
            allow_live=True,
        )
        search_runtime = SimpleNamespace(
            profile=profile,
            vector=vector,
            embedder=embedder,
            counter=counter,
            lock=threading.Lock(),
            close=lambda: None,
        )
        app = runtime.install(create_app(), search_runtime)
        with TestClient(app) as client:
            login = client.post(
                "/api/v1/auth/login", json={"username": username, "password": password}
            )
            if login.status_code != 200:
                raise RuntimeError("Smoke authentication failed")
            auth = {"Authorization": "Bearer " + login.json()["data"]["access_token"]}
            created = client.post("/api/v1/chat/sessions", headers=auth, json={})
            if created.status_code != 201:
                raise RuntimeError("Smoke session creation failed")
            for row in rows:
                print("Query:", row["id"], flush=True)
                response = client.post(
                    "/api/v1/chat/query",
                    headers=auth,
                    json={
                        "session_id": created.json()["data"]["id"],
                        "client_request_id": str(uuid.uuid4()),
                        "question": row["question"],
                    },
                )
                body = response.json()
                entry = {"id": row["id"], "http_status": response.status_code}
                summary["queries"].append(entry)
                if response.status_code != 200:
                    entry["error_code"] = body.get("error", {}).get("code", "unknown")
                    break  # No retry, fallback, remaining-question calls after a technical error.
                entry["answer_status"] = body["data"]["answer_status"]
                entry["citation_count"] = len(body["data"]["citations"])
    finally:
        try:
            if runtime is not None:
                runtime.export(output / "capture")
                run_replay(
                    ROOT,
                    output / "protocol.json",
                    output / "capture/capture.json",
                    output / "evaluation",
                    "dev",
                )
        finally:
            try:
                cleanup(sessions, vector, settings, user.workspace_id, user.id, keys)
                summary["cleanup_completed"] = True
            finally:
                vector.close()


def run(settings, *, live=False):
    url, profile = preflight(settings)
    if not live:
        return {
            "status": "preflight_passed",
            "model": settings.llm_model,
            "local_cache_verified": True,
            "index_version": profile["index_version"],
            "manual_free_tier_confirmed": True,
            "manual_quota_confirmed": True,
            "account_billing_independently_verified": False,
            "request_caps": CAPS,
            "model_calls": 0,
        }
    output = ROOT / ".cache" / SCOPE_ID
    # The fixed approved scope cannot be reset using a new run ID or CLI output path.
    output.mkdir(parents=True, exist_ok=False)
    summary = {
        "scope_id": SCOPE_ID,
        "started_at": datetime.now(UTC).isoformat(),
        "status": "setup_started",
        "dataset_kind": "synthetic_smoke",
        "questions_planned": 2,
        "request_caps": CAPS,
        "budget_usd": 0,
        "verified_invoice_cost_usd": None,
        "free_tier_confirmation": "manual_flags_and_user_authorization",
        "account_billing_independently_verified": False,
        "queries": [],
        "cleanup_completed": False,
        "human_review": "pending",
    }
    ledger = embedder = None
    try:
        counter = E5TokenCounter(settings.hf_home / "hub")
        rows, mapping, protocol, ledger = prepare_inputs(ROOT, output, settings, profile, counter)
        scope = fingerprint(ledger.grant)[:16]
        scoped = settings.model_copy(
            update={
                "qdrant_collection": "final_" + scope,
                "storage_dir": ROOT / "backend/.cache/final-capture" / scope,
            }
        )
        profile = {**profile, "collection_name": scoped.qdrant_collection}
        write_json(
            output / "profile.json",
            {key: value for key, value in profile.items() if key != "snapshot"},
        )
        embedder = LocalEmbedder(profile, scoped)
        with database(url) as sessions, native_http_events(summary):
            capture(
                sessions,
                scoped,
                profile,
                counter,
                embedder,
                output,
                rows,
                mapping,
                protocol,
                ledger,
                summary,
            )
        summary["status"] = (
            "completed"
            if len(summary["queries"]) == 2
            and all(row["http_status"] == 200 for row in summary["queries"])
            else "completed_with_errors"
        )
    except Exception as exc:
        # No raw exception/body/DSN/token/headers in logs or reports.
        summary["status"] = "failed"
        summary["error_type"] = type(exc).__name__
        code = getattr(exc, "code", None)
        if isinstance(code, str) and code in {
            "embedding_configuration_error",
            "embedding_timeout",
            "embedding_process_failed",
            "model_unavailable",
            "model_timeout",
        }:
            summary["error_code"] = code
    finally:
        if embedder is not None:
            summary["embedding_load_seconds"] = embedder.load_seconds
            embedder.close()
        summary["ledger"] = ledger.snapshot() if ledger is not None else None
        summary["finished_at"] = datetime.now(UTC).isoformat()
        write_json(output / "summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="One approved scope, no automatic reruns"
    )
    args = parser.parse_args(argv)
    try:
        result = run(Settings(_env_file=ROOT / ".env"), live=args.live)
    except Exception as exc:
        print(
            json.dumps({"status": "preflight_or_scope_blocked", "error_type": type(exc).__name__})
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"completed", "preflight_passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
