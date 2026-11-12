"""Smoke orchestration guards/labels on temporary synthetic data, no inference/network."""

import json
from contextlib import contextmanager

import httpx
import pytest

from app.core.config import Settings
from app.services.chunking import split_document
from app.services.gemini import BASE_URL, MODEL
from app.services.parsing import ParseLimits, _parse_inline
from eval import run_capture_smoke as smoke
from eval.final_eval import freeze, load_questions, read_json, verify
from eval.tests.test_final_eval import deny_network_and_project_corpus

deny_network_and_project_corpus = deny_network_and_project_corpus


def settings():
    return Settings(
        _env_file=None,
        database_url="postgresql+psycopg://fixture:fixture@127.0.0.1/fixture_dev",
        test_database_url="postgresql+psycopg://fixture:fixture@127.0.0.1/fixture_test",
        llm_base_url=BASE_URL,
        llm_model=MODEL,
        llm_api_key="fixture-key",
        llm_free_tier_confirmed=True,
        llm_quota_confirmed=True,
    )


class Counter:
    def __init__(self, *args):
        pass

    def count(self, value):
        return len(value) + 4


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    # Source copies pin a temporary fixture; no reviewed dataset is ever opened.
    for folder in ("backend/app/services", "backend/app/api", "eval"):
        (tmp_path / folder).mkdir(parents=True)
    for name in (
        "run_capture_smoke",
        "runtime_capture",
        "final_eval",
        "final_budget",
        "retrieval_gold",
        "span_metrics",
    ):
        (tmp_path / "eval" / (name + ".py")).write_text("# fixture source\n", encoding="utf-8")
    for name in ("answering", "chat", "gemini", "retrieval", "embeddings", "e5_runtime"):
        (tmp_path / "backend/app/services" / (name + ".py")).write_text(
            "# fixture\n", encoding="utf-8"
        )
    for name in ("chat", "search"):
        (tmp_path / "backend/app/api" / (name + ".py")).write_text("# fixture\n", encoding="utf-8")

    def prepare(path, format, config, counter):
        parsed = _parse_inline(path, format, ParseLimits())
        return parsed, split_document(parsed, counter)

    monkeypatch.setattr(smoke, "prepare_document", prepare)
    output = tmp_path / "scope"
    output.mkdir()
    result = smoke.prepare_inputs(
        tmp_path, output, settings(), {"index_version": "fixture"}, Counter()
    )
    return tmp_path, output, result


@pytest.mark.parametrize("field", ["llm_free_tier_confirmed", "llm_quota_confirmed", "llm_api_key"])
def test_preflight_fails_before_cache_without_confirmation(monkeypatch, field):
    from app.core.errors import AppError

    def forbidden(*args):
        pytest.fail("No cache/inference/DB after failed confirmation")

    monkeypatch.setattr(smoke, "frozen_profile", forbidden)
    with pytest.raises(AppError) as caught:
        smoke.preflight(
            settings().model_copy(update={field: None if field == "llm_api_key" else False})
        )
    assert caught.value.code == "model_unavailable"


def test_preflight_refuses_dev_database_and_remote_vectors(monkeypatch):
    monkeypatch.setattr(
        smoke, "frozen_profile", lambda config: pytest.fail("Must reject before cache")
    )
    config = settings()
    with pytest.raises(RuntimeError):
        smoke.preflight(config.model_copy(update={"test_database_url": config.database_url}))
    with pytest.raises(ValueError, match="local Qdrant"):
        smoke.preflight(config.model_copy(update={"qdrant_url": "https://example.invalid"}))


def test_synthetic_inputs_never_claim_human_review(inputs):
    root, output, (rows, mapping, protocol, ledger) = inputs
    assert len(rows) == 2 and sum(row["expected_abstain"] for row in rows) == 1
    assert protocol["dataset_kind"] == "synthetic_smoke"
    assert read_json(output / "data/corpus_manifest.json")["label_status"] == "synthetic_smoke"
    assert ",,,synthetic_fixture" in (output / "data/human_review.csv").read_text(encoding="utf-8")
    assert len(load_questions(root, protocol, "dev")) == 2
    assert ledger.grant["total"] == {"generateContent": 4, "countTokens": 14}
    assert len(ledger.grant["batches"]) == 2
    assert mapping["questions"][1]["evidence"] == []
    verify(root, protocol)


def test_synthetic_fixture_cannot_be_used_as_reviewed_or_heldout(inputs):
    root, output, (_, _, protocol, _) = inputs
    with pytest.raises(ValueError, match="two dev fixtures"):
        load_questions(root, protocol, "test", allow_heldout=True)
    with pytest.raises(ValueError, match="human-reviewed"):
        freeze(
            root,
            output / "data",
            output / "mapping.json",
            output / "config.json",
            output / "wrong.json",
        )


def test_preflight_run_has_zero_calls_and_creates_no_output(tmp_path, monkeypatch):
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    monkeypatch.setattr(smoke, "preflight", lambda config: (None, {"index_version": "fixture"}))
    result = smoke.run(settings())
    assert result["model_calls"] == 0
    assert not (tmp_path / ".cache").exists()


def test_fixed_scope_cannot_reset_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    monkeypatch.setattr(smoke, "preflight", lambda config: (None, {"index_version": "fixture"}))
    (tmp_path / ".cache" / smoke.SCOPE_ID).mkdir(parents=True)
    with pytest.raises(FileExistsError):
        smoke.run(settings(), live=True)


def test_setup_failure_never_invokes_capture_and_keeps_ledger(inputs, monkeypatch):
    root, output, prepared = inputs
    monkeypatch.setattr(smoke, "ROOT", root)
    monkeypatch.setattr(smoke, "preflight", lambda config: (None, {"index_version": "fixture"}))
    monkeypatch.setattr(smoke, "E5TokenCounter", Counter)
    monkeypatch.setattr(smoke, "prepare_inputs", lambda *args: prepared)
    monkeypatch.setattr(
        smoke,
        "LocalEmbedder",
        lambda *args: type("Fake", (), {"close": lambda self: None, "load_seconds": 0.0})(),
    )

    @contextmanager
    def broken(url):
        raise RuntimeError("Fixture storage failure")
        yield  # pragma: no cover

    monkeypatch.setattr(smoke, "database", broken)
    monkeypatch.setattr(
        smoke, "capture", lambda *args: pytest.fail("No capture after setup failure")
    )
    result = smoke.run(settings(), live=True)
    assert result["status"] == "failed" and result["queries"] == []
    assert result["ledger"]["total"] == {"generateContent": 0, "countTokens": 0}
    assert prepared[3].path.is_file()


def test_http_diagnostics_do_not_store_credentials_or_provider_body(monkeypatch):
    async def fake_send(*args, **kwargs):
        return httpx.Response(429, json={"error": {"message": "private-provider-body"}})

    monkeypatch.setattr(httpx.AsyncClient, "send", fake_send)
    summary = {}
    with smoke.native_http_events(summary):
        with httpx.Client() as unused_client:
            request = httpx.Request(
                "POST",
                BASE_URL + "/models/" + MODEL + ":countTokens",
                headers={"x-goog-api-key": "private-api-key"},
            )
            coroutine = httpx.AsyncClient.send(unused_client, request)
            # Both coroutines complete immediately: no event loop/socketpair/network.
            with pytest.raises(StopIteration):
                coroutine.send(None)
    assert summary["native_http_events"] == [{"action": "countTokens", "http_status": 429}]
    assert "private" not in json.dumps(summary)
