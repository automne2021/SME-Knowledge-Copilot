"""Real SQL/Qdrant dev capture; adversarial fixture, fake inference, no native calls."""

import json

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.core.errors import AppError
from app.services.embeddings import content_hash
from app.services.parsing import PARSER_VERSION
from app.services.vectors import QdrantIndex
from eval import adversarial_eval as adv
from eval.final_budget import RequestLedger, fingerprint
from eval.final_eval import read_json
from eval.tests.adversarial_support import inputs
from eval.tests.test_final_runner_sql import (
    forbid_live_inference,
    no_tokenizer,
    parser_child_packages,
    verified_tls_context,
)
from tests.database_safety import validate_test_database_url

__all__ = ["forbid_live_inference", "no_tokenizer", "parser_child_packages", "verified_tls_context"]


@pytest.mark.parametrize("failure", [None, "budget", "timeout"])
def test_adversarial_dev_storage_capture_stop_and_cleanup(tmp_path, monkeypatch, failure):
    settings = get_settings().model_copy(update={"retrieval_score_threshold": None})
    embedding = {"synthetic_adversarial_fixture": True, "dimension": 384}
    profile = {
        "index_version": content_hash({"fixture": "adversarial"}),
        "embedding_fingerprint": embedding,
        "embedding_hash": content_hash(embedding),
        "parser_version": PARSER_VERSION,
        "chunking_config": {"test_fake": True},
    }
    env = inputs(tmp_path, monkeypatch, settings, profile)
    output = env.output / "execution"
    output.mkdir()
    grant = adv.grant_for(env.protocol)
    ledger = RequestLedger.create(output / "requests.sqlite", grant)
    if failure == "budget":
        for _ in range(2):
            ledger.reserve("at14-answerable", "generateContent", "prior-synthetic-attempt")
    url = make_url(settings.test_database_url)
    url = url.set(
        database=url.database.removesuffix("_test") + "_at14_final_test",
        host="127.0.0.1" if url.host == "localhost" else url.host,
    )
    validate_test_database_url(url.render_as_string(hide_password=False), settings.database_url)
    closed = []

    class Embedder:
        def encode(self, texts):
            return [[1.0] + [0.0] * 383 for _ in texts]

        def encode_query(self, value, deadline=None):
            return self.encode([value])[0]

        def close(self):
            closed.append(True)

    calls = []

    class Provider:
        def count_tokens(self, payload, deadline):
            return 100

        def generate(self, payload, deadline):
            calls.append(payload)
            if failure == "timeout":
                raise AppError(504, "model_timeout", "Synthetic timeout")
            data = json.loads(payload["contents"][0]["parts"][0]["text"])
            abstain = data["question"] == adv.QUESTIONS[1][1]
            answer = {
                "answer_status": "insufficient_evidence" if abstain else "grounded",
                "claims": [] if abstain else [{"text": adv.QUOTE, "evidence_ids": ["E1"]}],
                "limitations": [],
                "missing_information": [],
                "conflict_detected": False,
            }
            return {
                "text": json.dumps(answer),
                "finish_reason": "STOP",
                "usage": None,
                "model_version": "fake",
            }

    from eval import final_runner

    loop = final_runner.query_loop
    monkeypatch.setattr(final_runner, "query_loop", lambda *args: loop(*args, sleep=lambda _: None))
    try:
        summary = adv.capture_run(
            env.root,
            output,
            env.protocol,
            adv.load_questions(env.root, env.protocol, "dev"),
            ledger,
            settings,
            profile,
            url,
            split="dev",
            inference_factory=lambda scoped, p: (env.counter, Embedder()),
            provider_factory=lambda _: Provider(),
            provider_kind="fake",
        )
        assert summary["cleanup_completed"] and summary["native_http_events"] == []
        runtime = read_json(output / "capture/execution.json")
        assert runtime["origin"] == "offline_fixture" and runtime["auth_override_present"] is False
        scores = read_json(output / "evaluation/metrics.json")
        assert scores["planned"] == 2 and scores["human"]["reviewed"] == 0
        if failure is None:
            assert scores["succeeded"] == 2 and len(calls) == 2
            assert ledger.snapshot()["total"]["generateContent"] == 2
            packet = adv.export_review(env.root)
            assert packet["reviewable"] == 2
            assert all(
                c["attack_in_final_context"]
                for c in read_json(env.output / "coverage.json")["cases"]
            )
            assert all(
                r["reviewer"] is None and r["score"]["correctness"] is None
                for r in read_json(env.output / "review/reviewer-a.json")
            )
        else:
            assert scores["attempted"] == scores["technical_errors"] == scores["not_attempted"] == 1
            assert len(calls) == (0 if failure == "budget" else 1)
            assert ledger.snapshot()["total"]["generateContent"] == (
                2 if failure == "budget" else 1
            )
    finally:
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        try:
            with engine.connect() as db:
                for table in (
                    "workspaces",
                    "users",
                    "documents",
                    "processing_jobs",
                    "query_runs",
                    "chat_messages",
                    "answer_citations",
                ):
                    assert db.scalar(text("select count(*) from " + table)) == 0
        finally:
            engine.dispose()
        vector = QdrantIndex(settings.qdrant_url, "final_" + fingerprint(grant)[:16], 5)
        try:
            assert vector._request("GET", allow_missing=True) is None
        finally:
            vector.close()
        storage = env.root / "backend/.cache/final-capture" / fingerprint(grant)[:16]
        assert not [p for p in storage.rglob("*") if p.is_file()]
        assert closed
