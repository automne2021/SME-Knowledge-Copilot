"""Frozen dev-only dense retrieval evaluation, production search/source APIs, zero LLM calls."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, delete, select, update  # noqa: E402
from sqlalchemy.engine import URL  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.db import get_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import (  # noqa: E402
    AuthToken,
    Chunk,
    Document,
    DocumentRevision,
    ProcessingJob,
    SourceBlock,
    User,
    Workspace,
)
from app.services.chunking import E5TokenCounter  # noqa: E402
from app.services.embeddings import LocalEmbedder, frozen_profile  # noqa: E402
from app.services.jobs import JobQueue  # noqa: E402
from app.services.vectors import QdrantIndex  # noqa: E402
from app.worker import IngestionWorker  # noqa: E402
from eval.ingestion_smoke import MIMES, MemorySampler  # noqa: E402
from eval.parser_mapping import digest  # noqa: E402
from eval.retrieval_gold import load_active_mapping, question_groups  # noqa: E402
from eval.span_metrics import aggregate, ranked_group_hits  # noqa: E402
from eval.validate_dataset import validate  # noqa: E402
from tests.database_safety import validate_test_database_url  # noqa: E402


def main():
    settings = get_settings()
    target = validate_test_database_url(settings.test_database_url, settings.database_url)
    dataset = ROOT / "eval/snapshots/reviewed-v1"
    validate(dataset, require_reviewed=True)
    corpus = json.loads((dataset / "corpus_manifest.json").read_text(encoding="utf-8"))
    config_path = ROOT / "eval/configs/dense.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    mapping_path = ROOT / "eval/mappings/reviewed-v1-source-v1-e5-350-v1.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    if mapping["parent_manifest_sha256"] != digest(dataset / "corpus_manifest.json"):
        raise ValueError("Canonical mapping parent hash mismatch")
    questions = [
        q
        for line in (dataset / "questions.jsonl").read_text(encoding="utf-8").splitlines()
        if (q := json.loads(line))["split"] == "dev"
    ]
    mapped_questions = {q["id"]: q for q in mapping["questions"]}
    run_id = datetime.now(UTC).strftime("retrieval_dev_%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8]
    output = ROOT / "eval/reports" / run_id
    output.mkdir(parents=True, exist_ok=False)
    storage = ROOT / "backend/.cache/s7" / run_id[-8:]
    saved = (
        settings.storage_dir,
        settings.qdrant_collection,
        settings.llm_api_key,
        settings.llm_base_url,
    )
    settings.storage_dir, settings.qdrant_collection = storage, "s7_dev_" + run_id[-8:]
    settings.llm_api_key = settings.llm_base_url = None
    profile = frozen_profile(settings)
    if (
        profile["index_version"] != config["expected_index_version"]
        or settings.retrieval_candidate_k != config["candidate_k"]
        or settings.retrieval_top_k != config["production_top_k"]
        or settings.retrieval_score_threshold != config["score_threshold"]
    ):
        raise ValueError("Runtime differs from frozen baseline; version config and reindex first")
    test_url = URL.create(
        "postgresql+psycopg",
        username=target.username,
        password=target.password,
        host=target.host,
        port=target.port,
        database=target.database,
    )
    engine = create_engine(test_url, connect_args={"connect_timeout": 5})
    sessions = sessionmaker(engine, expire_on_commit=False)
    with sessions() as db:
        if db.scalar(
            select(ProcessingJob.id)
            .where(
                ProcessingJob.kind == "ingest",
                ProcessingJob.status.in_(["queued", "running", "retry_wait"]),
            )
            .limit(1)
        ):
            raise RuntimeError("Run dev eval in isolation; unrelated active jobs exist")
    vector = QdrantIndex(
        settings.qdrant_url, settings.qdrant_collection, settings.vector_timeout_seconds
    )
    vector.ensure_collection(profile["embedding_hash"])
    embedder = LocalEmbedder(profile, settings)
    counter = E5TokenCounter(settings.hf_home / "hub")
    worker = IngestionWorker(JobQueue(sessions, settings), vector, embedder, counter, profile)
    app = create_app()

    def db_dependency():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = db_dependency
    app.state.search_runtime = SimpleNamespace(
        profile=profile,
        vector=vector,
        embedder=embedder,
        counter=counter,
        lock=threading.Lock(),
        close=lambda: None,
    )
    workspace_id, admin_id, member_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    memory = MemorySampler()
    memory.thread.start()
    rows, ingestion, uploaded = [], [], {}
    report = {
        "run_id": run_id,
        "split": "dev",
        "test_queries_used": 0,
        "llm_calls": 0,
        "api_model_spend_usd": 0,
        "synthetic": True,
        "real_embedding": True,
        "query_model_already_warm_from_ingestion": True,
        "cleanup_completed": False,
        "dataset_manifest_sha256": digest(dataset / "corpus_manifest.json"),
        "mapping_sha256": digest(mapping_path),
        "baseline_config_sha256": digest(config_path),
        "profile": {k: v for k, v in profile.items() if k != "snapshot"},
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        ),
        "challenger": {
            "model": "BAAI/bge-m3",
            "status": "deferred",
            "reason": "not_cached_and_cpu_memory_margin_not_validated",
            "available_ram_before_bytes": memory.available_before,
        },
        "failure_cases": [],
    }
    # Persist the selected protocol before evaluating any dev query, not after seeing scores.
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    try:
        with sessions() as db:
            db.add(Workspace(id=workspace_id, name="Synthetic Step 07 dev evaluation"))
            db.flush()
            encoded = hash_password("dev-eval-synthetic-password")
            for user_id, role in [(admin_id, "knowledge_admin"), (member_id, "member")]:
                db.add(
                    User(
                        id=user_id,
                        workspace_id=workspace_id,
                        username="s7." + user_id.hex,
                        email=user_id.hex + "@example.invalid",
                        display_name=role,
                        role=role,
                        password_hash=encoded,
                    )
                )
            db.commit()
        with TestClient(app) as client:

            def auth(user_id):
                result = client.post(
                    "/api/v1/auth/login",
                    json={
                        "username": "s7." + user_id.hex,
                        "password": "dev-eval-synthetic-password",
                    },
                )
                assert result.status_code == 200
                return {"Authorization": "Bearer " + result.json()["data"]["access_token"]}

            admin_auth, member_auth = auth(admin_id), auth(member_id)
            for entry in corpus["documents"]:
                path = dataset / entry["path"]
                result = client.post(
                    "/api/v1/documents",
                    headers=admin_auth,
                    files={"file": (path.name, path.read_bytes(), MIMES[entry["format"]])},
                )
                assert result.status_code == 202
                data = result.json()["data"]
                terminal = worker.run_once()
                assert terminal["status"] == "completed"
                uploaded[entry["document_id"]] = uuid.UUID(data["document_id"])
                ingestion.append(
                    {
                        "reference": entry["document_id"],
                        "corpus_version": entry["version"],
                        "document_id": data["document_id"],
                        "worker": terminal,
                    }
                )
                source = client.get(
                    f"/api/v1/documents/{data['document_id']}/content", headers=member_auth
                )
                assert (
                    source.status_code == 200
                    and source.headers["x-content-type-options"] == "nosniff"
                )
                if entry["format"] != "docx":
                    assert source.content == path.read_bytes()
            with sessions() as db:
                loaded = load_active_mapping(db, workspace_id, uploaded, mapping, profile)
            report["active_mapping_verified"] = True
            # Prove loader drift fails rather than silently reducing the evaluation denominator.
            with sessions() as db:
                block = db.scalar(
                    select(SourceBlock).where(
                        SourceBlock.revision_id.in_(
                            select(DocumentRevision.id).where(
                                DocumentRevision.document_id.in_(uploaded.values())
                            )
                        )
                    )
                )
                block.normalized_text = "injected mapping drift"
                db.flush()
                try:
                    load_active_mapping(db, workspace_id, uploaded, mapping, profile)
                except ValueError:
                    report["mapping_drift_guard_verified"] = True
                else:
                    raise AssertionError("Corrupt mapping was not rejected")
                db.rollback()
            for question in questions:
                groups = question_groups(question, mapped_questions[question["id"]], loaded)
                started = time.perf_counter()
                result = client.post(
                    "/api/v1/search",
                    headers=member_auth,
                    json={
                        "query": question["question"],
                        "top_k": config["evaluation_top_k"],
                        "mode": "dense",
                    },
                )
                row = {
                    "id": question["id"],
                    "question_type": question["question_type"],
                    "query": question["question"],
                    "required_groups": sorted(groups),
                    "expected_abstain": question["expected_abstain"],
                    "http_status": result.status_code,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                }
                if result.status_code != 200:
                    row.update(
                        status="failed",
                        error_code=result.json()["error"]["code"],
                        ranked_group_hits=[],
                    )
                else:
                    data = result.json()["data"]
                    hits = data["hits"]
                    for hit in hits:
                        if loaded["chunk_text"].get(hit["chunk_id"]) != hit["excerpt"]:
                            raise ValueError("Search text differs from canonical active source")
                    ranks = ranked_group_hits(
                        groups, [loaded["chunk_spans"][hit["chunk_id"]] for hit in hits]
                    )
                    row.update(
                        status="completed",
                        hits=hits,
                        trace=data["trace"],
                        timings_ms=data["timings_ms"],
                        ranked_group_hits=[sorted(found) for found in ranks],
                    )
                    if hits:
                        source = client.get(hits[0]["source"]["chunk_url"], headers=member_auth)
                        assert (
                            source.status_code == 200
                            and source.json()["data"]["text"] == hits[0]["excerpt"]
                        )
                    at_five = set().union(*ranks[:5]) if ranks else set()
                    if groups and at_five != set(groups):
                        report["failure_cases"].append(
                            {
                                "id": question["id"],
                                "category": "ranking_miss_at_5",
                                "missing_groups": sorted(set(groups) - at_five),
                                "parser_and_chunk_mapping_verified": True,
                                "threshold_and_llm_context_budget_applied": False,
                            }
                        )
                    if not groups and hits:
                        report["failure_cases"].append(
                            {
                                "id": question["id"],
                                "category": "unanswerable_has_candidates_with_cutoff_disabled",
                                "generation_not_evaluated": True,
                            }
                        )
                rows.append(row)
            report["metrics"] = aggregate(rows, config["metric_ks"])
            report["status"] = (
                "completed"
                if report["metrics"]["technical_failures"] == 0
                else "completed_with_errors"
            )
    except Exception as exc:
        report["status"], report["error_type"] = "failed", type(exc).__name__
        raise
    finally:
        memory.stop.set()
        memory.thread.join(3)
        report["peak_parent_and_children_rss_bytes"] = memory.peak
        report["embedding_load_seconds"] = embedder.load_seconds
        embedder.close()
        try:
            vector._request("DELETE")
            with sessions() as db:
                ids = select(Document.id).where(Document.workspace_id == workspace_id)
                revisions = select(DocumentRevision.id).where(DocumentRevision.document_id.in_(ids))
                keys = db.scalars(
                    select(DocumentRevision.storage_key).where(
                        DocumentRevision.document_id.in_(ids)
                    )
                ).all()
                db.execute(
                    update(Document)
                    .where(Document.workspace_id == workspace_id)
                    .values(status="failed", active_revision_id=None, active_generation_id=None)
                )
                db.execute(delete(ProcessingJob).where(ProcessingJob.document_id.in_(ids)))
                db.execute(delete(Chunk).where(Chunk.revision_id.in_(revisions)))
                db.execute(delete(SourceBlock).where(SourceBlock.revision_id.in_(revisions)))
                db.execute(delete(DocumentRevision).where(DocumentRevision.document_id.in_(ids)))
                db.execute(delete(Document).where(Document.workspace_id == workspace_id))
                users = select(User.id).where(User.workspace_id == workspace_id)
                db.execute(delete(AuthToken).where(AuthToken.user_id.in_(users)))
                db.execute(delete(User).where(User.workspace_id == workspace_id))
                db.execute(delete(Workspace).where(Workspace.id == workspace_id))
                db.commit()
            for key in keys:
                path = (storage / key).resolve()
                assert path.is_relative_to(storage.resolve())
                path.unlink(missing_ok=True)
            report["cleanup_completed"] = True
        finally:
            vector.close()
            engine.dispose()
            (
                settings.storage_dir,
                settings.qdrant_collection,
                settings.llm_api_key,
                settings.llm_base_url,
            ) = saved
            (output / "manifest.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            (output / "per_question.jsonl").write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            (output / "ingestion.json").write_text(
                json.dumps(ingestion, indent=2) + "\n", encoding="utf-8"
            )
            sources = list((ROOT / "backend/app").rglob("*.py")) + [
                Path(__file__),
                ROOT / "eval/span_metrics.py",
                ROOT / "eval/retrieval_gold.py",
                ROOT / "eval/metrics.py",
                config_path,
            ]
            snapshot = output / "source_snapshot"
            snapshot.mkdir()
            hashes = {}
            for source in sources:
                name = source.relative_to(ROOT).as_posix().replace("/", "__") + ".txt"
                (snapshot / name).write_bytes(source.read_bytes())
                hashes[str(source.relative_to(ROOT))] = digest(source)
            (output / "source_sha256.json").write_text(
                json.dumps(hashes, indent=2) + "\n", encoding="utf-8"
            )
    print(
        json.dumps(
            {
                "report": str(output.relative_to(ROOT)),
                "status": report["status"],
                "metrics": report["metrics"],
                "failures": report["failure_cases"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    main()
