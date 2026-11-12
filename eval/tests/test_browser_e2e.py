"""Guards for the disposable E2E harness; no browser/model/service calls."""

import json
import shutil
import uuid
from types import SimpleNamespace

import pytest

from app.core.errors import AppError
from eval import browser_e2e as browser
from eval import run_capture_smoke as smoke
from eval.final_budget import BudgetExceeded, RequestLedger
from eval.final_eval import load_questions, sha256, verify, write_json
from eval.tests import test_capture_smoke as smoke_fixtures
from eval.tests.test_capture_smoke import Counter, settings
from eval.tests.test_final_eval import deny_network_and_project_corpus  # noqa: F401

inputs = smoke_fixtures.inputs


@pytest.fixture
def controller():
    space = uuid.uuid4()
    users = {
        role: SimpleNamespace(id=uuid.uuid4(), workspace_id=space) for role in ("admin", "member")
    }
    return browser.Controller(None, None, None, [], None, None, None, users, None)


def test_only_owned_document_can_be_deleted(controller, monkeypatch):
    identity = uuid.uuid4()
    monkeypatch.setattr(controller, "document", lambda: SimpleNamespace(id=identity))
    assert controller.allow("DELETE", "/api/v1/documents/" + str(identity))
    assert not controller.allow("DELETE", "/api/v1/documents/" + str(uuid.uuid4()))
    assert not controller.allow("POST", "/api/v1/jobs/any/retry")
    assert not controller.allow("PATCH", "/api/v1/documents/" + str(identity))


def test_no_delete_before_exact_fixture_upload(controller, monkeypatch):
    def missing():
        raise AppError(503, "e2e_corpus_not_ready", "fixture")

    monkeypatch.setattr(controller, "document", missing)
    assert not controller.allow("DELETE", "/api/v1/documents/" + str(uuid.uuid4()))


def test_post_delete_question_cannot_start_while_ready(controller, monkeypatch):
    controller.rows = [{"id": "admin-after-delete", "question": "after"}]
    monkeypatch.setattr(controller, "document", lambda: SimpleNamespace(status="ready"))
    with pytest.raises(AppError) as caught:
        controller.observer_for(None, SimpleNamespace(question="after"), None)
    assert caught.value.code == "e2e_phase_not_ready"
    assert controller.runtime is None


def test_before_publication_cannot_initialize_model(controller, monkeypatch):
    monkeypatch.setattr(controller, "document", lambda: SimpleNamespace(status="processing"))
    with pytest.raises(AppError) as caught:
        controller.observer_for(None, SimpleNamespace(question="before"), None)
    assert caught.value.code == "e2e_corpus_not_ready"
    assert controller.runtime is None


def test_six_lifecycle_fixtures_have_one_global_cap_and_zero_post_delete_calls(inputs):
    root, _, _ = inputs
    output = root / "browser-scope"
    output.mkdir()
    rows, mapping, protocol, ledger = smoke.prepare_inputs(
        root,
        output,
        settings(),
        {"index_version": "fixture"},
        Counter(),
        question_plan=browser.PLAN,
        scope_id=browser.SCOPE,
        caps=browser.CAPS,
        synthetic_e2e=True,
    )
    assert len(rows) == 6 and protocol["dataset_kind"] == "synthetic_browser_e2e"
    assert len(load_questions(root, protocol, "dev")) == 6
    verify(root, protocol)
    assert ledger.grant["total"] == {"generateContent": 8, "countTokens": 28}
    for role in ("admin", "member"):
        assert ledger.grant["batches"][role + "-after-delete"] == {
            "generateContent": 0,
            "countTokens": 0,
        }
    assert len(mapping["questions"]) == 6
    with pytest.raises(ValueError, match="never held-out"):
        load_questions(root, protocol, "test", allow_heldout=True)


@pytest.fixture
def stopped_scope(inputs):
    root, _, _ = inputs
    output = root / ".cache" / browser.SCOPE
    output.mkdir(parents=True)
    _, _, protocol, ledger = smoke.prepare_inputs(
        root,
        output,
        settings(),
        {"index_version": "fixture"},
        Counter(),
        question_plan=browser.PLAN,
        scope_id=browser.SCOPE,
        caps=browser.CAPS,
        synthetic_e2e=True,
    )
    for name in protocol["files_sha256"]:
        target = output / "frozen-root" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
    bundle = root / "frontend/dist"
    bundle.mkdir(parents=True)
    (bundle / "index.html").write_text("fixture", encoding="utf-8")
    write_json(output / "ui-bundle-sha256.json", {"index.html": sha256(bundle / "index.html")})
    summary = {
        "scope": browser.SCOPE,
        "cleanup_completed": True,
        "api_events": [],
        "worker": [],
        "native_http_events": [],
        "ledger": ledger.snapshot(),
    }
    write_json(output / "summary.json", summary)
    (output / "finish").touch()
    return root, output, ledger, summary


def retry_child(tmp_path, parent):
    grant = {**parent.grant, "scope_id": browser.SCOPE + "-retry-01", "protocol_sha256": "b" * 64}
    return RequestLedger.create(tmp_path / "child.sqlite", grant)


def test_retry_reuses_parent_global_cap_and_pins_one_attempt(stopped_scope, tmp_path):
    root, _, parent, _ = stopped_scope
    assert browser.retry_parent(root).snapshot() == parent.snapshot()
    child = retry_child(tmp_path, parent)
    retry = browser.RetryLedger(parent, child)
    retry.bind_runtime("c" * 64)
    retry.reserve("admin-answer", "generateContent", "one")
    parent.reserve("admin-answer", "generateContent", "other-process")
    with pytest.raises(BudgetExceeded):
        retry.reserve("admin-answer", "generateContent", "one")
    assert retry.snapshot()["global_allowance"]["total"]["generateContent"] == 2
    assert child.snapshot()["total"]["generateContent"] == 1
    with pytest.raises(ValueError, match="Runtime plan differs"):
        parent.bind_runtime("d" * 64)
    with pytest.raises(ValueError, match="reservations or a runtime binding"):
        browser.retry_parent(root)
    with pytest.raises(BudgetExceeded):
        retry.reserve("admin-after-delete", "countTokens", "after")


def test_child_failure_keeps_parent_reservation(stopped_scope, tmp_path, monkeypatch):
    _, _, parent, _ = stopped_scope
    child = retry_child(tmp_path, parent)
    retry = browser.RetryLedger(parent, child)

    def fail(*args):
        raise OSError("fixture ledger failure")

    monkeypatch.setattr(child, "reserve", fail)
    with pytest.raises(OSError):
        retry.reserve("member-answer", "countTokens", "one")
    assert parent.snapshot()["total"]["countTokens"] == 1
    assert child.snapshot()["total"]["countTokens"] == 0


@pytest.mark.parametrize(
    "change",
    ["cleanup", "events", "reservation", "binding", "bundle", "archive", "grant", "missing-ledger"],
)
def test_retry_refuses_unsafe_parent(stopped_scope, change):
    root, output, ledger, summary = stopped_scope
    if change == "cleanup":
        summary["cleanup_completed"] = False
    elif change == "events":
        summary["native_http_events"] = [{"status": 200}]
    elif change == "reservation":
        ledger.reserve("admin-answer", "countTokens", "old")
    elif change == "binding":
        ledger.bind_runtime("a" * 64)
    elif change == "bundle":
        (root / "frontend/dist/index.html").write_text("changed", encoding="utf-8")
    elif change == "archive":
        (output / "frozen-root/eval/final_budget.py").write_text("changed", encoding="utf-8")
    elif change == "grant":
        (output / "grant.json").write_text(
            json.dumps({**ledger.grant, "total": {"generateContent": 9, "countTokens": 28}}),
            encoding="utf-8",
        )
    else:
        ledger.path.unlink()
    (output / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        browser.retry_parent(root)


def test_retry_cannot_expand_batch_allowance(stopped_scope, tmp_path):
    _, _, parent, _ = stopped_scope
    child = RequestLedger.create(
        tmp_path / "expanded.sqlite",
        {
            **parent.grant,
            "scope_id": browser.SCOPE + "-retry-01",
            "total": {"generateContent": 9, "countTokens": 28},
        },
    )
    with pytest.raises(ValueError, match="cannot expand"):
        browser.RetryLedger(parent, child)
