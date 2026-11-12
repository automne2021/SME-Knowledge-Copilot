"""Prepare opaque reviewed inputs offline; native execution needs a separate approval.

No app, credentials, database, tokenizer or model imports on the offline path.
The approval JSON is a technical gate, not a substitute for the user's authorization.
"""

from __future__ import annotations

import argparse
import shutil
import time
import uuid
from pathlib import Path

from eval.final_budget import RequestLedger, fingerprint, request_bound
from eval.final_eval import freeze, inside, load_questions, read_json, sha256, verify, write_json
from eval.final_pacing import POLICY

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ".cache/final-reviewed-baseline-20261111-paced"
DATASET = "eval/snapshots/reviewed-v1"
MAPPING = "eval/mappings/reviewed-v1-source-v1-e5-350-v1.json"
CONFIG = "eval/configs/final_baseline.json"
EXTRA_FILES = (
    "scripts/run-final-eval.py",
    "backend/requirements.lock",
    "backend/requirements-ai-cpu.lock",
    "backend/requirements-worker-cpu.lock",
)


def prepare(root, output, dataset=DATASET, mapping=MAPPING, config=CONFIG):
    """Freeze candidate bytes, without decoding held-out question text or issuing a grant."""
    root = Path(root).resolve()
    output = inside(root, output)
    if not output.is_relative_to(root / ".cache"):
        raise ValueError("Candidate belongs under .cache, outside reviewed inputs")
    cfg = read_json(inside(root, config))
    if (
        cfg.get("expected_test_queries") != 30
        or cfg.get("production_top_k") != 5
        or cfg.get("concurrency") != 1
        or cfg.get("budget_usd") != 0
        or cfg.get("request_pacing") != POLICY
    ):
        raise ValueError("Expected fixed 30-question/top5/sequential/zero-dollar candidate")
    output.mkdir(parents=True, exist_ok=False)
    source_paths = sorted(
        p.relative_to(root).as_posix()
        for p in (*(root / "backend/app").rglob("*.py"), *(root / "eval").glob("*.py"))
    )
    protocol = freeze(root, dataset, mapping, config, output / "protocol.json", source_paths)
    extra = {name: sha256(inside(root, name)) for name in EXTRA_FILES}
    draft = {
        "schema": 1,
        "scope_id": output.name,
        "protocol_sha256": fingerprint(protocol),
        "split": "test",
        "query_count": 30,
        "total": request_bound(30, 5),
        "batch_per_query": request_bound(1, 5),
        "budget_usd": 0,
        "approval": "pending",
        "extra_files_sha256": extra,
    }
    write_json(output / "request-plan.json", draft)
    write_json(output / "approval-template.json", approval_template(draft))
    archive = output / "frozen-root"
    archive.mkdir()
    for name in {**protocol["files_sha256"], **extra}:
        target = archive / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(inside(root, name), target)
    shutil.copyfile(output / "protocol.json", archive / "protocol.json")
    verify_candidate(root, output)
    return draft


def approval_template(plan):
    return {
        "state": "pending",
        "approval_reference": None,
        "request_plan_sha256": fingerprint(plan),
        "budget_usd": 0,
        "free_tier_confirmed": False,
        "quota_confirmed": False,
    }


def verify_candidate(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    protocol, plan = (read_json(output / name) for name in ("protocol.json", "request-plan.json"))
    verify(root, protocol)
    if read_json(output / "frozen-root/protocol.json") != protocol:
        raise ValueError("Archived protocol changed")
    verify(output / "frozen-root", protocol)
    for name, digest in plan["extra_files_sha256"].items():
        if (
            sha256(inside(root, name)) != digest
            or sha256(inside(output / "frozen-root", name)) != digest
        ):
            raise ValueError("Bootstrap/dependency bytes changed after freeze")
    if (
        protocol.get("dataset_kind") != "human_reviewed"
        or plan
        != {
            "schema": 1,
            "scope_id": output.name,
            "protocol_sha256": fingerprint(protocol),
            "split": "test",
            "query_count": 30,
            "total": request_bound(30, 5),
            "batch_per_query": request_bound(1, 5),
            "budget_usd": 0,
            "approval": "pending",
            "extra_files_sha256": plan["extra_files_sha256"],
        }
        or set(plan["extra_files_sha256"]) != set(EXTRA_FILES)
    ):
        raise ValueError("Request plan differs from fixed pending candidate")
    return protocol, plan


def authorize(root, output, approval):
    """Fail before loading held-out questions, importing app runtime or creating resources."""
    protocol, plan = verify_candidate(root, output)
    if not isinstance(approval, dict):
        raise ValueError("Separate approval must be an object")
    expected = approval_template(plan)
    expected.update(
        state="approved",
        free_tier_confirmed=True,
        quota_confirmed=True,
        approval_reference=approval.get("approval_reference"),
    )
    if (
        approval != expected
        or not isinstance(approval.get("approval_reference"), str)
        or not approval["approval_reference"].strip()
    ):
        raise ValueError("Separate approval/free-tier/quota confirmation required; no live calls")
    return protocol, plan


def query_loop(client, auth, session_id, rows, summary, *, sleep=time.sleep, interval=5):
    """One client ID per question, concurrency1; stop on error, no replay or fallback."""
    for index, row in enumerate(rows):
        if index:
            sleep(interval)
        entry = {"id": row["id"], "http_status": None}
        summary["queries"].append(entry)
        try:
            response = client.post(
                "/api/v1/chat/query",
                headers=auth,
                json={
                    "session_id": session_id,
                    "client_request_id": str(uuid.uuid4()),
                    "question": row["question"],
                },
            )
        except Exception as exc:
            entry["error_type"] = type(exc).__name__
            raise
        entry["http_status"] = response.status_code
        if response.status_code != 200:
            entry["error_code"] = response.json().get("error", {}).get("code", "unknown")
            break


def execute(root, output, approval):
    """Future opt-in execution. Not called in the offline preparation batch."""
    root, output = Path(root).resolve(), Path(output).resolve()
    protocol, plan = authorize(root, output, approval)
    execution = output / "execution"
    if execution.exists():
        raise ValueError("One-shot execution exists; preserve ledger, do not reset/retry")
    rows = load_questions(root, protocol, "test", allow_heldout=True)
    if len(rows) != 30:
        raise ValueError("Frozen held-out split must have exactly 30 questions")
    # Native imports occur only after the separate gate and split validation.
    from app.core.config import Settings
    from app.services.answering import PROMPT_VERSION
    from eval.run_capture_smoke import preflight

    settings = Settings(_env_file=root / ".env")
    cfg = read_json(inside(root, protocol["config"]))
    if cfg["prompt_version"] != PROMPT_VERSION:
        raise ValueError("Prompt label differs from frozen production prompt")
    fields = {
        "model": "embedding_model",
        "revision": "embedding_revision",
        "dimension": "embedding_dimension",
        "candidate_k": "retrieval_candidate_k",
        "production_top_k": "retrieval_top_k",
        "score_threshold": "retrieval_score_threshold",
    }
    fields.update(
        {
            key: key
            for key in cfg
            if key.startswith("llm_")
            or key in {"chunk_size_tokens", "chunk_overlap_tokens", "query_timeout_seconds"}
        }
    )
    if any(getattr(settings, target) != cfg[key] for key, target in fields.items()):
        raise ValueError("Runtime settings differ from frozen baseline")
    url, profile = preflight(settings)
    if profile["index_version"] != cfg["expected_index_version"]:
        raise ValueError("Local embedding/index profile differs from freeze")
    execution.mkdir(exist_ok=False)
    grant = {
        "scope_id": plan["scope_id"],
        "protocol_sha256": fingerprint(protocol),
        "total": plan["total"],
        "batches": {q["id"]: plan["batch_per_query"] for q in rows},
    }
    write_json(execution / "grant.json", grant)
    write_json(execution / "approval.json", approval)
    ledger = RequestLedger.create(execution / "requests.sqlite", grant)
    return native_capture(root, execution, protocol, rows, ledger, settings, profile, url)


def native_capture(root, output, protocol, rows, ledger, settings, profile, url):
    from app.services.chunking import E5TokenCounter
    from app.services.embeddings import LocalEmbedder
    from app.services.gemini import GeminiProvider

    def inference(scoped, profile):
        return E5TokenCounter(scoped.hf_home / "hub"), LocalEmbedder(profile, scoped)

    url = url.set(
        database=url.database.removesuffix("_smoke_test") + "_final_test",
        host="127.0.0.1" if url.host == "localhost" else url.host,
    )
    return capture_run(
        root,
        output,
        protocol,
        rows,
        ledger,
        settings,
        profile,
        url,
        inference_factory=inference,
        provider_factory=GeminiProvider,
        split="test",
        provider_kind="native_gemini",
        allow_live=True,
        allow_heldout=True,
    )


def capture_run(
    root,
    output,
    protocol,
    rows,
    ledger,
    settings,
    profile,
    url,
    *,
    inference_factory,
    provider_factory,
    split,
    provider_kind="fake",
    allow_live=False,
    allow_heldout=False,
):
    """Shared SQL orchestration; injected fake inference retains offline_fixture origin."""
    import asyncio
    import io
    import secrets
    import threading
    from contextlib import nullcontext
    from types import SimpleNamespace
    from unittest.mock import patch

    from fastapi.testclient import TestClient
    from starlette.datastructures import UploadFile

    from app.core import config
    from app.core.security import hash_password
    from app.models import User, Workspace
    from app.services.jobs import JobQueue
    from app.services.uploads import register_upload, store_stream
    from app.services.vectors import QdrantIndex
    from app.worker import IngestionWorker
    from eval.final_eval import run_replay
    from eval.final_pacing import native_pacing
    from eval.retrieval_gold import load_active_mapping
    from eval.run_capture_smoke import cleanup, database, native_http_events, parser_packages
    from eval.runtime_capture import CaptureRuntime, SqlCanonicalSources
    from tests.database_safety import validate_test_database_url

    validate_test_database_url(url.render_as_string(hide_password=False), settings.database_url)
    if not url.database.endswith("_final_test"):
        raise ValueError("Final orchestration requires a dedicated *_final_test database")
    scope = fingerprint(ledger.grant)[:16]
    scoped = settings.model_copy(
        update={
            "qdrant_collection": "final_" + scope,
            "storage_dir": root / "backend/.cache/final-capture" / scope,
        }
    )
    from app.main import create_app

    profile = {**profile, "collection_name": scoped.qdrant_collection}
    embedder, vector = None, None
    user = SimpleNamespace(id=uuid.uuid4(), workspace_id=uuid.uuid4())
    username, password = "final." + user.id.hex, secrets.token_urlsafe(24)
    keys, uploaded, runtime = [], {}, None
    summary = {
        "scope_id": ledger.grant["scope_id"],
        "split": split,
        "provider_kind": provider_kind,
        "queries": [],
        "ingestion": [],
        "cleanup_completed": False,
        "budget_usd": 0,
        "invoice_cost_verified_usd": None,
        "human_review": "pending",
        "mode": "end_to_end_dense",
        "warmup_queries": 0,
        "concurrency": 1,
    }
    try:
        verify(root, protocol)
        mapping = read_json(inside(root, protocol["mapping"]))
        dataset = inside(root, protocol["dataset"])
        manifest = read_json(dataset / "corpus_manifest.json")
        counter, embedder = inference_factory(scoped, profile)
        vector = QdrantIndex(
            scoped.qdrant_url, scoped.qdrant_collection, scoped.vector_timeout_seconds
        )
        with patch.object(config, "get_settings", lambda: scoped), database(url) as sessions:
            try:
                with sessions() as db:
                    db.add(Workspace(id=user.workspace_id, name="Disposable final reviewed eval"))
                    db.flush()
                    db.add(
                        User(
                            id=user.id,
                            workspace_id=user.workspace_id,
                            username=username,
                            email=user.id.hex + "@final.invalid",
                            display_name="Final fixture",
                            role="knowledge_admin",
                            password_hash=hash_password(password),
                        )
                    )
                    db.commit()
                vector.ensure_collection(profile["embedding_hash"])
                pacing = (
                    native_pacing(
                        output / "pacing.jsonl",
                        read_json(inside(root, protocol["config"]))["request_pacing"],
                        summary,
                    )
                    if provider_kind == "native_gemini"
                    else nullcontext()
                )
                with parser_packages(ROOT), native_http_events(summary), pacing:
                    for doc in manifest["documents"]:
                        data = inside(dataset, doc["path"]).read_bytes()
                        stored = asyncio.run(
                            store_stream(
                                UploadFile(io.BytesIO(data)),
                                scoped.storage_dir,
                                user.workspace_id,
                                doc["format"],
                                settings.max_upload_mb * 1024**2,
                            )
                        )
                        keys.append(stored.storage_key)
                        with sessions() as db:
                            result = register_upload(
                                db, user, Path(doc["path"]).name, doc["format"], stored
                            )
                        uploaded[doc["document_id"]] = result["document_id"]
                        job = IngestionWorker(
                            JobQueue(sessions, scoped), vector, embedder, counter, profile
                        ).run_once()
                        summary["ingestion"].append(job)
                        if (
                            not job
                            or job["status"] != "completed"
                            or job["job_id"] != str(result["job_id"])
                        ):
                            raise RuntimeError("Final corpus ingestion failed; no automatic retry")
                    with sessions() as db:
                        load_active_mapping(db, user.workspace_id, uploaded, mapping, profile)
                    specs = [
                        {
                            "id": q["id"],
                            "question": q["question"],
                            "user_id": str(user.id),
                            "workspace_id": str(user.workspace_id),
                            "document_ids": [],
                            "batch": q["id"],
                        }
                        for q in rows
                    ]
                    runtime = CaptureRuntime(
                        root,
                        protocol,
                        split,
                        specs,
                        ledger,
                        SqlCanonicalSources(
                            sessions, user.workspace_id, uploaded, mapping, profile
                        ),
                        scoped,
                        provider_factory,
                        provider_kind=provider_kind,
                        allow_live=allow_live,
                        allow_heldout=allow_heldout,
                    )
                    search = SimpleNamespace(
                        profile=profile,
                        vector=vector,
                        embedder=embedder,
                        counter=counter,
                        lock=threading.Lock(),
                        close=lambda: None,
                    )
                    with TestClient(runtime.install(create_app(), search)) as client:
                        logged = client.post(
                            "/api/v1/auth/login", json={"username": username, "password": password}
                        )
                        if logged.status_code != 200:
                            raise RuntimeError("Final authentication failed")
                        auth = {"Authorization": "Bearer " + logged.json()["data"]["access_token"]}
                        session = client.post("/api/v1/chat/sessions", headers=auth, json={})
                        if session.status_code != 201:
                            raise RuntimeError("Final session creation failed")
                        query_loop(client, auth, session.json()["data"]["id"], rows, summary)
            finally:
                try:
                    if runtime is not None:
                        runtime.export(output / "capture")
                        run_replay(
                            root,
                            output.parent / "protocol.json",
                            output / "capture/capture.json",
                            output / "evaluation",
                            split,
                            allow_heldout=allow_heldout,
                        )
                finally:
                    cleanup(sessions, vector, scoped, user.workspace_id, user.id, keys)
                    summary["cleanup_completed"] = True
    except Exception as exc:
        summary["orchestration_error_type"] = type(exc).__name__
        raise
    finally:
        try:
            if embedder is not None:
                embedder.close()
        finally:
            try:
                if vector is not None:
                    vector.close()
            finally:
                summary["ledger"] = ledger.snapshot()
                write_json(output / "summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify", "capture"))
    parser.add_argument("--candidate", default=CANDIDATE)
    parser.add_argument("--approval", type=Path)
    args = parser.parse_args(argv)
    output = inside(ROOT, args.candidate)
    if args.command == "prepare":
        prepare(ROOT, args.candidate)
        print("Offline candidate frozen; held-out text not decoded, grant pending, model calls0")
    elif args.command == "verify":
        verify_candidate(ROOT, output)
        print("Candidate source/input/archive hashes verified; no model calls")
    else:
        if not args.approval:
            raise ValueError("Separate approved execution JSON required; no live calls")
        execute(ROOT, output, read_json(args.approval))
    return 0
