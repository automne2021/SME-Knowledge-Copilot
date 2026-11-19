"""Shared final orchestration against real storage, synthetic corpus, fake inference."""

import json
import ssl
import uuid
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from app.core import config
from app.core.errors import AppError
from app.services.chunking import E5TokenCounter, split_document
from app.services.embeddings import content_hash
from app.services.parsing import PARSER_VERSION, parse_file
from app.services.vectors import QdrantIndex
from eval import final_runner as runner
from eval.final_budget import RequestLedger, fingerprint
from eval.final_eval import freeze, read_json, sha256, write_json
from eval.tests.test_runtime_capture_sql import (
    Counter,
    Embedder,
    forbid_live_inference,
    parser_child_packages,
)
from tests.database_safety import validate_test_database_url

# Reuse the external HTTP/native model/corpus guards, not the old SQL fixture.
__all__ = ["forbid_live_inference", "parser_child_packages"]
POLICY = "Synthetic policy: reimbursement deadline is 30 days."


@pytest.fixture(scope="module")
def verified_tls_context():
    # Avoid repeated slow native cafile loading in this Windows embedded Python.
    # Keep CERT_REQUIRED/check_hostname and the installed certifi CA bundle.
    import certifi

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cadata=Path(certifi.where()).read_text(encoding="ascii"))
    return context


@pytest.fixture(autouse=True)
def no_tokenizer(monkeypatch, verified_tls_context):
    import httpx._transports.default as transport

    original = transport.create_ssl_context

    def context(verify=True, cert=None, trust_env=True):
        if verify is True and cert is None:
            return verified_tls_context
        return original(verify=verify, cert=cert, trust_env=trust_env)

    monkeypatch.setattr(transport, "create_ssl_context", context)

    def forbidden(*args, **kwargs):
        raise AssertionError("Native tokenizer construction prohibited")

    monkeypatch.setattr(E5TokenCounter, "__init__", forbidden)


@pytest.fixture
def fixture_run(tmp_path, monkeypatch):
    settings = config.get_settings().model_copy(
        update={
            "retrieval_score_threshold": None,
            "llm_api_key": None,
            "llm_free_tier_confirmed": False,
            "llm_quota_confirmed": False,
        }
    )
    target = validate_test_database_url(settings.test_database_url, settings.database_url)
    url = URL.create(
        "postgresql+psycopg",
        username=target.username,
        password=target.password,
        # Explicit IPv4 loopback avoids the embedded Windows libpq localhost stall.
        host="127.0.0.1" if target.host == "localhost" else target.host,
        port=target.port,
        database=target.database.removesuffix("_test") + "_final_test",
    )
    env = SimpleNamespace(
        root=tmp_path,
        settings=settings,
        url=url,
        count=0,
        generate=0,
        closed=False,
        failure=None,
        documents=1,
        queries=2,
    )
    original_loop = runner.query_loop
    # Avoid real 5s gaps only in fake tests; production default stays unchanged.
    monkeypatch.setattr(
        runner,
        "query_loop",
        lambda *args: original_loop(*args, sleep=lambda _: None),
    )

    def execute(*, documents=1, budget=2, mapping_drift=False, broken_document=False):
        data = tmp_path / "data"
        data.mkdir()
        docs, mapped, blocks = [], {}, []
        for index in range(documents):
            name = f"policy-{index}"
            source = data / (name + ".txt")
            source.write_text(POLICY + f" Policy number {index}.", encoding="utf-8")
            parsed = parse_file(source, "txt")
            chunks = split_document(parsed, Counter())
            docs.append(
                {
                    "document_id": name,
                    "path": source.name,
                    "format": "txt",
                    "sha256": sha256(source),
                }
            )
            mapped[name] = {
                "sha256": sha256(source),
                "blocks": [asdict(b) for b in parsed.blocks],
                "chunks": [asdict(c) for c in chunks],
            }
            blocks += [asdict(b) for b in parsed.blocks]
        if mapping_drift:
            mapped["policy-0"]["blocks"][0]["raw_text"] += " drift"
        if broken_document:
            # Actual parser rejection, not a mocked worker result.
            # Pass the upload signature check, then fail UTF-8 decoding in the real worker.
            source.write_bytes(b"\xff")
            docs[-1]["sha256"] = sha256(source)
            mapped[docs[-1]["document_id"]]["sha256"] = sha256(source)
        questions = [
            {
                "id": f"synthetic-final-{i}",
                "split": "dev",
                "family_id": f"family-{i}",
                "question": f"What is the synthetic deadline in example {i}?",
                "expected_answer": POLICY,
                "expected_abstain": False,
                "gold_evidence": [
                    {
                        "evidence_id": "gold-policy",
                        "evidence_group_id": "deadline",
                        "document_id": "policy-0",
                        "quote": POLICY,
                    }
                ],
            }
            for i in range(env.queries)
        ]
        (data / "questions.jsonl").write_text(
            "".join(json.dumps(q) + "\n" for q in questions), encoding="utf-8"
        )
        write_json(data / "source_blocks.json", blocks)
        (data / "human_review.csv").write_text(
            "question_id,annotator,reviewer,status\n"
            + "".join(q["id"] + ",fixture-author,fixture-reviewer,approved\n" for q in questions),
            encoding="utf-8",
        )
        write_json(
            data / "corpus_manifest.json",
            {
                # Synthetic fixture contract; not the team's reviewed dataset/output scores.
                "label_status": "human_reviewed",
                "documents": docs,
                "fixtures": [],
                "questions_sha256": sha256(data / "questions.jsonl"),
                "source_blocks_sha256": sha256(data / "source_blocks.json"),
                "human_review_sha256": sha256(data / "human_review.csv"),
            },
        )
        write_json(
            tmp_path / "mapping.json",
            {
                "parent_manifest_sha256": sha256(data / "corpus_manifest.json"),
                "parser_version": PARSER_VERSION,
                "documents": mapped,
                "questions": [
                    {
                        "id": q["id"],
                        "evidence": [
                            {
                                **q["gold_evidence"][0],
                                "parser_spans": [
                                    {
                                        "block_id": mapped["policy-0"]["blocks"][0]["block_id"],
                                        "char_start": 0,
                                        "char_end": len(POLICY),
                                        "role": "content",
                                    }
                                ],
                            }
                        ],
                    }
                    for q in questions
                ],
            },
        )
        index = content_hash({"synthetic_final": True, "parser": PARSER_VERSION})
        write_json(
            tmp_path / "config.json",
            {
                "production_top_k": 5,
                "evaluation_top_k": 10,
                "expected_index_version": index,
            },
        )
        protocol = freeze(
            tmp_path, "data", "mapping.json", "config.json", tmp_path / "protocol.json"
        )
        grant = {
            "scope_id": "synthetic-final-" + uuid.uuid4().hex,
            "protocol_sha256": fingerprint(protocol),
            "total": {"generateContent": budget * env.queries, "countTokens": 14},
            "batches": {q["id"]: {"generateContent": budget, "countTokens": 7} for q in questions},
        }
        env.ledger = RequestLedger.create(tmp_path / "requests.sqlite", grant)
        env.scope = fingerprint(grant)[:16]
        env.storage = tmp_path / "backend/.cache/final-capture" / env.scope
        env.collection = "final_" + env.scope
        embedding = {"synthetic_final": True, "dimension": 384}
        profile = {
            "embedding_fingerprint": embedding,
            "embedding_hash": content_hash(embedding),
            "index_version": index,
            "parser_version": PARSER_VERSION,
            "chunking_config": {"fake_counter": True},
            "collection_name": env.collection,
        }

        class FakeEmbedder(Embedder):
            def close(self):
                env.closed = True

        class Provider:
            def count_tokens(self, payload, deadline):
                env.count += 1
                return 100

            def generate(self, payload, deadline):
                env.generate += 1
                if env.failure:
                    # Same public error contract as GeminiProvider after an HTTP timeout.
                    raise AppError(504, "model_timeout", "Synthetic timeout")
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

        env.output = tmp_path / "execution"
        env.output.mkdir()
        return runner.capture_run(
            tmp_path,
            env.output,
            protocol,
            questions,
            env.ledger,
            settings,
            profile,
            url,
            inference_factory=lambda *_: (Counter(), FakeEmbedder()),
            provider_factory=lambda _: Provider(),
            split="dev",
        )

    env.execute = execute
    yield env
    if hasattr(env, "scope"):
        # Independently check the orchestration cleaned its own scope after success/failure.
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        cfg = Config(str(Path(__file__).resolve().parents[2] / "backend/alembic.ini"))
        cfg.set_main_option(
            "script_location", str(Path(__file__).resolve().parents[2] / "backend/alembic")
        )
        try:
            with engine.connect() as db:
                assert (
                    db.scalar(text("select version_num from alembic_version"))
                    == ScriptDirectory.from_config(cfg).get_current_head()
                )
                for table in (
                    "workspaces",
                    "users",
                    "documents",
                    "document_revisions",
                    "source_blocks",
                    "chunks",
                    "processing_jobs",
                    "chat_sessions",
                    "chat_messages",
                    "query_runs",
                    "answer_citations",
                    "auth_tokens",
                ):
                    assert db.scalar(text(f"select count(*) from {table}")) == 0, table
        finally:
            engine.dispose()
        vector = QdrantIndex(settings.qdrant_url, env.collection, 5)
        try:
            assert vector._request("GET", allow_missing=True) is None
        finally:
            vector.close()
        assert not [p for p in env.storage.rglob("*") if p.is_file()]
        assert env.closed


def test_final_ten_document_orchestration(fixture_run):
    env = fixture_run
    summary = env.execute(documents=10)
    assert len(summary["ingestion"]) == 10
    assert all(j["status"] == "completed" for j in summary["ingestion"])
    assert [q["http_status"] for q in summary["queries"]] == [200, 200]
    assert summary["cleanup_completed"] and summary["native_http_events"] == []
    assert env.generate == 2 and summary["ledger"]["total"]["generateContent"] == 2
    assert summary["ledger"]["total"]["countTokens"] == env.count
    execution = read_json(env.output / "capture/execution.json")
    assert execution["origin"] == "offline_fixture" and execution["provider_kind"] == "fake"
    assert execution["auth_override_present"] is False
    scores = read_json(env.output / "evaluation/metrics.json")
    assert scores["planned"] == scores["succeeded"] == 2
    assert scores["human"]["reviewed"] == 0


@pytest.mark.parametrize("failure", ["budget", "timeout"])
def test_final_error_stops_preserves_coverage_and_cleanup(fixture_run, failure):
    env = fixture_run
    env.failure = failure == "timeout"
    summary = env.execute(budget=0 if failure == "budget" else 2)
    assert len(summary["queries"]) == 1 and summary["queries"][0]["http_status"] != 200
    assert env.generate == (1 if failure == "timeout" else 0)
    assert summary["ledger"]["total"]["generateContent"] == env.generate
    assert summary["cleanup_completed"]
    scores = read_json(env.output / "evaluation/metrics.json")
    assert scores["planned"] == 2 and scores["attempted"] == 1
    assert scores["not_attempted"] == scores["technical_errors"] == 1


@pytest.mark.parametrize("failure", ["mapping", "ingestion"])
def test_final_prequery_failure_has_receipt_and_cleanup(fixture_run, failure):
    env = fixture_run
    with pytest.raises((ValueError, RuntimeError)):
        env.execute(mapping_drift=failure == "mapping", broken_document=failure == "ingestion")
    summary = read_json(env.output / "summary.json")
    assert summary["queries"] == [] and summary["cleanup_completed"]
    assert summary["ledger"]["total"] == {"countTokens": 0, "generateContent": 0}
    assert env.generate == env.count == 0
    assert not (env.output / "capture").exists()
