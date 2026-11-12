"""Offline final-runner guards, opaque test input preparation, stop-on-error execution."""

import json
from types import SimpleNamespace

import pytest

from eval import final_runner as runner
from eval.tests import test_final_eval as fixtures

frozen = fixtures.frozen
deny_network_and_project_corpus = fixtures.deny_network_and_project_corpus


@pytest.fixture
def candidate(frozen):
    root, _, protocol, *_ = frozen
    cfg = {
        "expected_test_queries": 30,
        "production_top_k": 5,
        "concurrency": 1,
        "budget_usd": 0,
        "request_pacing": runner.POLICY,
    }
    (root / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    for name in runner.EXTRA_FILES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# temporary offline fixture\n", encoding="utf-8")
    output = root / ".cache/candidate"
    plan = runner.prepare(
        root, ".cache/candidate", protocol["dataset"], protocol["mapping"], "config.json"
    )
    return root, output, plan


def test_prepare_does_not_decode_heldout_or_create_grant(frozen, monkeypatch):
    root, _, protocol, *_ = frozen
    for name in runner.EXTRA_FILES:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture", encoding="utf-8")
    cfg = {
        "expected_test_queries": 30,
        "production_top_k": 5,
        "concurrency": 1,
        "budget_usd": 0,
        "request_pacing": runner.POLICY,
    }
    (root / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.setattr(runner, "load_questions", lambda *a, **k: pytest.fail("No held-out decode"))
    plan = runner.prepare(
        root, ".cache/candidate", protocol["dataset"], protocol["mapping"], "config.json"
    )
    assert plan["total"] == {"generateContent": 60, "countTokens": 210}
    assert plan["approval"] == "pending"
    assert not list((root / ".cache/candidate").rglob("*.sqlite"))
    assert not (root / ".cache/candidate/execution").exists()


@pytest.mark.parametrize("change", ["pending", "quota", "free", "reference", "plan", "budget"])
def test_no_approval_cannot_load_questions_or_touch_runtime(candidate, monkeypatch, change):
    root, output, plan = candidate
    approval = runner.approval_template(plan)
    approval.update(
        state="approved",
        approval_reference="fixture-only-not-real-authorization",
        free_tier_confirmed=True,
        quota_confirmed=True,
    )
    key, value = {
        "pending": ("state", "pending"),
        "quota": ("quota_confirmed", False),
        "free": ("free_tier_confirmed", False),
        "reference": ("approval_reference", ""),
        "plan": ("request_plan_sha256", "0" * 64),
        "budget": ("budget_usd", 1),
    }[change]
    approval[key] = value
    monkeypatch.setattr(runner, "load_questions", lambda *a, **k: pytest.fail("Held-out opened"))
    monkeypatch.setattr(runner, "native_capture", lambda *a, **k: pytest.fail("Runtime reached"))
    with pytest.raises(ValueError, match="Separate approval"):
        runner.execute(root, output, approval)
    assert not (output / "execution").exists()


def test_valid_gate_is_bound_to_exact_pending_candidate(candidate):
    root, output, plan = candidate
    approval = runner.approval_template(plan)
    approval.update(
        state="approved",
        approval_reference="fixture-only",
        free_tier_confirmed=True,
        quota_confirmed=True,
    )
    assert runner.authorize(root, output, approval)[1] == plan
    with pytest.raises(FileExistsError):
        runner.prepare(root, ".cache/candidate", "data", "mapping.json", "config.json")


@pytest.mark.parametrize("change", ["source", "archive", "archive-protocol", "lock", "plan"])
def test_drift_fails_before_execution(candidate, change):
    root, output, plan = candidate
    if change == "source":
        (root / "config.json").write_text("{}", encoding="utf-8")
    elif change == "archive":
        (output / "frozen-root/config.json").write_text("{}", encoding="utf-8")
    elif change == "lock":
        (root / runner.EXTRA_FILES[-1]).write_text("changed", encoding="utf-8")
    elif change == "archive-protocol":
        (output / "frozen-root/protocol.json").write_text("{}", encoding="utf-8")
    else:
        (output / "request-plan.json").write_text(
            json.dumps({**plan, "total": {"generateContent": 61, "countTokens": 210}}),
            encoding="utf-8",
        )
    with pytest.raises(ValueError):
        runner.verify_candidate(root, output)


def test_existing_execution_is_not_resumed_or_reset(candidate, monkeypatch):
    root, output, plan = candidate
    approval = runner.approval_template(plan)
    approval.update(
        state="approved",
        approval_reference="fixture-only",
        free_tier_confirmed=True,
        quota_confirmed=True,
    )
    (output / "execution").mkdir()
    monkeypatch.setattr(runner, "load_questions", lambda *a, **k: pytest.fail("No rerun"))
    with pytest.raises(ValueError, match="One-shot"):
        runner.execute(root, output, approval)


def test_loop_keeps_error_and_stops_without_retry_or_concurrency():
    calls, waits = [], []

    def post(path, **kwargs):
        calls.append(kwargs["json"])
        status = 200 if len(calls) == 1 else 503
        return SimpleNamespace(
            status_code=status, json=lambda: {"error": {"code": "model_unavailable"}}
        )

    summary = {"queries": []}
    rows = [{"id": str(i), "question": "fixture"} for i in range(30)]
    runner.query_loop(SimpleNamespace(post=post), {}, "session", rows, summary, sleep=waits.append)
    assert len(calls) == len(summary["queries"]) == 2
    assert len({call["client_request_id"] for call in calls}) == 2
    assert summary["queries"][-1]["error_code"] == "model_unavailable"
    assert waits == [5]


def test_candidate_does_not_allow_output_over_reviewed_data(frozen):
    root, *_ = frozen
    with pytest.raises(ValueError, match="under .cache"):
        runner.prepare(root, "data/new")


def test_transport_exception_keeps_receipt_and_never_retries():
    def post(*args, **kwargs):
        raise TimeoutError("fixture-only")

    summary = {"queries": []}
    with pytest.raises(TimeoutError):
        runner.query_loop(
            SimpleNamespace(post=post),
            {},
            "session",
            [{"id": "one", "question": "fixture"}],
            summary,
        )
    assert summary["queries"] == [{"id": "one", "http_status": None, "error_type": "TimeoutError"}]


def test_approved_wrong_size_still_fails_before_native_import(candidate):
    root, output, plan = candidate
    approval = runner.approval_template(plan)
    approval.update(
        state="approved",
        approval_reference="fixture-only",
        free_tier_confirmed=True,
        quota_confirmed=True,
    )
    with pytest.raises(ValueError, match="exactly 30"):
        runner.execute(root, output, approval)
    assert not (output / "execution").exists()
