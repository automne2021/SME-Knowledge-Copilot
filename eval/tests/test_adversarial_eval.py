"""Fixed-scope guards and transparent payload auditing; no network/inference/held-out reads."""

import json
import time

import httpx
import pytest

from app.core.config import Settings
from app.core.errors import AppError
from app.services.answering import request_payload
from app.services.gemini import BASE_URL, MODEL, GeminiProvider
from eval import adversarial_eval as adv
from eval.final_budget import BudgetExceeded, GuardedProvider, RequestLedger, fingerprint
from eval.final_eval import load_questions, read_json
from eval.tests.adversarial_support import inputs


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("External HTTP forbidden in AT-R14 unit tests")

    monkeypatch.setattr(httpx.Client, "send", forbidden)
    monkeypatch.setattr(httpx.AsyncClient, "send", forbidden)


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://fixture:fixture@127.0.0.1/fixture_dev",
        test_database_url="postgresql+psycopg://fixture:fixture@127.0.0.1/fixture_test",
        llm_api_key="fixture-key",
        llm_base_url=BASE_URL,
        llm_model=MODEL,
        llm_free_tier_confirmed=True,
        llm_quota_confirmed=True,
        retrieval_score_threshold=None,
    )
    return inputs(tmp_path, monkeypatch, settings, {"index_version": "fixture-index"})


def approved(env):
    return adv.approval_template(env.plan) | {
        "state": "approved",
        "approval_reference": "synthetic test authorization",
        "free_tier_confirmed": True,
        "quota_confirmed": True,
    }


def test_prepare_is_two_synthetic_dev_queries_not_human_review_or_execution(prepared):
    env = prepared
    protocol, plan = adv.verify_prepared(env.root)
    rows = load_questions(env.root, protocol, "dev")
    assert [r["id"] for r in rows] == [r[0] for r in adv.QUESTIONS]
    assert [r["expected_abstain"] for r in rows] == [False, True]
    assert protocol["dataset_kind"] == "synthetic_smoke"
    assert plan["total"] == {"generateContent": 4, "countTokens": 14} and plan["budget_usd"] == 0
    assert not (env.output / "execution").exists()
    assert adv.ATTACK in (env.output / "data/policy.txt").read_text(encoding="utf-8")
    assert ",,,synthetic_fixture" in (env.output / "data/human_review.csv").read_text(
        encoding="utf-8"
    )
    with pytest.raises(ValueError):
        load_questions(env.root, protocol, "test", allow_heldout=True)


@pytest.mark.parametrize(
    "name",
    [
        "data/policy.txt",
        "mapping.json",
        "config.json",
        "frozen-root/protocol.json",
        "frozen-root/eval/adversarial_eval.py",
    ],
)
def test_frozen_input_archive_drift_blocks_execution(prepared, name):
    env = prepared
    with (env.output / name).open("a", encoding="utf-8") as f:
        f.write(" drift")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        adv.verify_prepared(env.root)


@pytest.mark.parametrize("name", [adv.BOOTSTRAP, adv.BASELINE, "eval/adversarial_eval.py"])
def test_source_bootstrap_and_baseline_drift(prepared, name):
    env = prepared
    with (env.root / name).open("a", encoding="utf-8") as f:
        f.write(" drift")
    with pytest.raises(ValueError):
        adv.verify_prepared(env.root)


def test_caps_scope_cannot_be_expanded_by_editing_request_plan(prepared):
    env = prepared
    plan = read_json(env.output / "request-plan.json")
    plan["total"]["countTokens"] = 999
    (env.output / "request-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError):
        adv.verify_prepared(env.root)


@pytest.mark.parametrize(
    "change",
    [
        None,
        {"state": "pending"},
        {"free_tier_confirmed": False},
        {"quota_confirmed": False},
        {"approval_reference": None},
        {"request_plan_sha256": "0" * 64},
    ],
)
def test_scoped_approval_rejected_before_runtime(prepared, monkeypatch, change):
    env = prepared
    monkeypatch.setattr(
        adv, "runtime", lambda root: pytest.fail("No runtime before valid approval")
    )
    approval = None if change is None else approved(env) | change
    with pytest.raises(ValueError):
        adv.execute(env.root, approval)
    assert not (env.output / "execution").exists()


def test_scope_and_execution_are_one_shot_before_runtime(prepared, monkeypatch):
    env = prepared
    monkeypatch.setattr(
        adv, "runtime", lambda root: pytest.fail("No runtime when fixed output exists")
    )
    with pytest.raises(FileExistsError):
        adv.prepare(env.root)
    (env.output / "execution").mkdir()
    with pytest.raises(FileExistsError):
        adv.execute(env.root, approved(env))


def test_grant_is_separate_fixed_per_question_budget(prepared):
    env = prepared
    ledger = RequestLedger.create(env.output / "test.sqlite", adv.grant_for(env.protocol))
    for _ in range(2):
        ledger.reserve("at14-answerable", "generateContent", "fixture")
    with pytest.raises(BudgetExceeded):
        ledger.reserve("at14-answerable", "generateContent", "fixture")
    for _ in range(7):
        ledger.reserve("at14-unanswerable", "countTokens", "fixture")
    with pytest.raises(BudgetExceeded):
        ledger.reserve("at14-unanswerable", "countTokens", "fixture")
    assert ledger.snapshot()["total"] == {"countTokens": 7, "generateContent": 2}


def test_payload_audit_delegates_without_changing_native_payload_or_response(prepared, monkeypatch):
    env = prepared
    seen = []
    response = {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}

    def post(instance, action, payload, deadline):
        seen.append((action, payload))
        return response

    monkeypatch.setattr(GeminiProvider, "_post", post)
    payload = request_payload(
        adv.QUESTIONS[0][1], [{"evidence_id": "E1", "excerpt": adv.POLICY}], env.settings
    )
    audit = env.output / "audit"
    audit.mkdir()
    provider = GeminiProvider(env.settings)
    with adv.native_payload_audit(env.root, audit, env.settings, fingerprint(env.plan)):
        assert provider._post("generateContent", payload, time.monotonic() + 1) is response
    assert seen == [("generateContent", payload)] and seen[0][1] is payload
    assert GeminiProvider._post is post
    event = read_json_lines(audit / "payload-audit.jsonl")[0]
    assert event["attack_in_evidence"] and event["tools_absent"]
    assert event["response_function_calls"] == 0 and event["error_type"] is None
    text = (audit / "payload-audit.jsonl").read_text(encoding="utf-8")
    assert "fixture-key" not in text and adv.POLICY not in text


def read_json_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_count_tokens_wrapper_and_repair_system_remain_unchanged(prepared, monkeypatch):
    env = prepared
    seen = []

    def post(instance, action, payload, deadline):
        seen.append((action, payload))
        return {"totalTokens": 37}

    monkeypatch.setattr(GeminiProvider, "_post", post)
    payload = request_payload(adv.QUESTIONS[1][1], [], env.settings, True)
    with adv.native_payload_audit(env.root, env.output, env.settings, fingerprint(env.plan)):
        assert GeminiProvider(env.settings).count_tokens(payload, time.monotonic() + 1) == 37
    assert seen[0][0] == "countTokens"
    assert seen[0][1]["generateContentRequest"] == {"model": "models/" + MODEL, **payload}
    event = read_json_lines(env.output / "payload-audit.jsonl")[0]
    assert event["tools_absent"] and not event["attack_in_evidence"]


@pytest.mark.parametrize("failure", [False, True])
def test_execute_uses_dev_scope_and_keeps_ledger_after_setup_failure(
    prepared, monkeypatch, failure
):
    from sqlalchemy.engine import make_url

    env = prepared
    monkeypatch.setattr(
        adv,
        "runtime",
        lambda root: (
            env.settings,
            env.profile,
            env.counter,
            make_url("postgresql+psycopg://fixture:fixture@127.0.0.1/fixture_smoke_test"),
        ),
    )
    seen = []

    def capture(root, output, protocol, rows, ledger, settings, profile, url, **kwargs):
        seen.append(kwargs)
        assert [r["split"] for r in rows] == ["dev", "dev"]
        assert kwargs["split"] == "dev" and kwargs["allow_live"]
        assert "allow_heldout" not in kwargs
        assert kwargs["provider_factory"] is GeminiProvider
        assert kwargs["provider_kind"] == "native_gemini"
        assert url.database == "fixture_at14_final_test"
        assert ledger.grant == adv.grant_for(protocol)
        if failure:
            raise RuntimeError("synthetic setup failure")
        return {"synthetic_orchestration_only": True}

    monkeypatch.setattr(adv, "capture_run", capture)
    if failure:
        with pytest.raises(RuntimeError):
            adv.execute(env.root, approved(env))
    else:
        assert adv.execute(env.root, approved(env))["synthetic_orchestration_only"]
    assert len(seen) == 1
    assert (env.output / "execution/requests.sqlite").is_file()
    with pytest.raises(FileExistsError):
        adv.execute(env.root, approved(env))


@pytest.mark.parametrize("change", ["tools", "system", "question"])
def test_payload_audit_refuses_unplanned_tools_system_or_question(prepared, monkeypatch, change):
    env = prepared
    monkeypatch.setattr(
        GeminiProvider, "_post", lambda *args: pytest.fail("No transport for invalid payload")
    )
    payload = request_payload(adv.QUESTIONS[0][1], [], env.settings)
    if change == "tools":
        payload["tools"] = []
    elif change == "system":
        payload["systemInstruction"] = {"parts": [{"text": "altered"}]}
    else:
        payload["contents"][0]["parts"][0]["text"] = json.dumps(
            {"question": "foreign", "evidence": []}
        )
    with adv.native_payload_audit(env.root, env.output, env.settings, fingerprint(env.plan)):
        with pytest.raises(ValueError):
            GeminiProvider(env.settings)._post("generateContent", payload, time.monotonic() + 1)


def test_transport_failure_burns_reservation_and_audit_does_not_retry(prepared, monkeypatch):
    env = prepared

    def failed(*args):
        raise AppError(503, "model_unavailable", "synthetic error")

    monkeypatch.setattr(GeminiProvider, "_post", failed)
    ledger = RequestLedger.create(env.output / "test.sqlite", adv.grant_for(env.protocol))
    payload = request_payload(adv.QUESTIONS[0][1], [], env.settings)
    with adv.native_payload_audit(env.root, env.output, env.settings, fingerprint(env.plan)):
        provider = GuardedProvider(
            lambda: GeminiProvider(env.settings), ledger, "at14-answerable", "synthetic"
        )
        with pytest.raises(AppError):
            provider.generate(payload, time.monotonic() + 1)
    assert ledger.snapshot()["total"]["generateContent"] == 1
    event = read_json_lines(env.output / "payload-audit.jsonl")[0]
    assert event["error_type"] == "AppError" and event["response_function_calls"] is None
