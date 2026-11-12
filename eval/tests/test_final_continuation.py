"""Temporary ledgers/corpus only; no held-out data, network or native inference."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from eval import final_continuation as cont
from eval.final_budget import (
    BudgetExceeded,
    GuardedProvider,
    LedgerUnavailable,
    RequestLedger,
    fingerprint,
    request_bound,
)
from eval.final_eval import read_json, run_replay, sha256, write_json
from eval.final_runner import EXTRA_FILES, POLICY
from eval.final_runner import prepare as prepare_parent
from eval.tests import test_final_eval as fixtures

frozen = fixtures.frozen
deny_network_and_project_corpus = fixtures.deny_network_and_project_corpus


@pytest.fixture
def linked(tmp_path):
    grant = {
        "scope_id": "temporary-parent",
        "protocol_sha256": "a" * 64,
        "total": request_bound(4),
        "batches": {q: request_bound(1) for q in ("done", "failed", "u1", "u2")},
    }
    parent = RequestLedger.create(tmp_path / "parent.sqlite", grant)
    parent.bind_runtime("a" * 64)
    for q in ("done", "failed"):
        parent.reserve(q, "generateContent", q)
        for _ in range(7):
            parent.reserve(q, "countTokens", q)
    baseline = cont.ledger_state(parent)
    child = RequestLedger.create(
        tmp_path / "child.sqlite",
        {
            "scope_id": "temporary-parent-continuation-01",
            "protocol_sha256": "a" * 64,
            "total": request_bound(2),
            "batches": {q: request_bound(1) for q in ("u1", "u2")},
        },
    )
    claim = tmp_path / "claim.json"
    wrapper = cont.ContinuationLedger.claim(parent, child, baseline, claim)
    return wrapper, parent, child, baseline, claim


def test_link_preserves_original_binding_and_reservations(linked):
    wrapper, parent, child, baseline, _ = linked
    wrapper.bind_runtime("b" * 64)
    wrapper.reserve("u1", "countTokens", "u1:fixture")
    assert cont.ledger_state(parent)["binding"] == baseline["binding"] == ["a" * 64]
    assert cont.ledger_state(child)["binding"] == ["b" * 64]
    assert wrapper.snapshot()["total"]["countTokens"] == 1
    assert wrapper.snapshot()["global_allowance"]["total"]["countTokens"] == 15


def test_second_claim_and_already_attempted_batch_refused(linked):
    wrapper, parent, child, baseline, claim = linked
    with pytest.raises(FileExistsError):
        cont.ContinuationLedger.claim(parent, child, baseline, claim)
    with pytest.raises(ValueError, match="outside"):
        wrapper.reserve("failed", "generateContent", "foreign")
    assert cont.ledger_state(parent) == baseline


def test_parent_budget_blocks_even_when_child_empty(linked):
    wrapper, parent, child, _, _ = linked
    for _ in range(7):
        parent.reserve("u1", "countTokens", wrapper.prefix + "fixture")
    with pytest.raises(BudgetExceeded):
        wrapper.reserve("u1", "countTokens", "fixture")
    assert child.snapshot()["total"]["countTokens"] == 0


def test_child_failure_never_refunds_parent_or_calls_provider(linked, monkeypatch):
    wrapper, parent, child, baseline, _ = linked

    def unavailable(*args):
        raise OSError("fixture storage unavailable")

    monkeypatch.setattr(child, "reserve", unavailable)
    provider = GuardedProvider(
        lambda: pytest.fail("No provider may be constructed"), wrapper, "u1", "fixture"
    )
    with pytest.raises(LedgerUnavailable):
        provider.generate({}, 999)
    assert parent.snapshot()["total"]["generateContent"] == 3
    assert len(cont.ledger_state(parent)["reservations"]) == len(baseline["reservations"]) + 1


@pytest.mark.parametrize("change", ["claim", "binding", "old-reservation", "foreign"])
def test_tampered_history_fails_closed(linked, change):
    wrapper, parent, _, baseline, claim = linked
    if change == "claim":
        claim.write_text("{}", encoding="utf-8")
    elif change == "foreign":
        parent.reserve("u1", "countTokens", "unexpected-client")
    else:
        with sqlite3.connect(parent.path) as db:
            if change == "binding":
                db.execute("update runtime_binding set plan_sha256=?", ("c" * 64,))
            else:
                db.execute("delete from reservations where id=?", (baseline["reservations"][0][0],))
    with pytest.raises(ValueError):
        wrapper.reserve("u1", "countTokens", "fixture")


def test_concurrent_reservations_never_exceed_original_batch(linked):
    wrapper, parent, child, _, _ = linked

    def reserve(index):
        try:
            wrapper.reserve("u1", "generateContent", str(index))
            return True
        except BudgetExceeded:
            return False

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(reserve, range(12)))
    assert sum(results) == 2
    assert parent.snapshot()["batches"]["u1"]["generateContent"] == 2
    assert child.snapshot()["batches"]["u1"]["generateContent"] == 2


@pytest.fixture
def prepared(frozen):
    root, _, _, capture, _, observation = frozen
    data = root / "data"
    first_question = json.loads((data / "questions.jsonl").read_text().splitlines()[0])
    questions = [
        {
            **first_question,
            "id": f"q{i:03}",
            "family_id": f"q{i:03}",
            "split": "test",
            "question": f"Synthetic fixture question {i}",
        }
        for i in range(1, 31)
    ]
    (data / "questions.jsonl").write_text(
        "".join(json.dumps(q) + "\n" for q in questions), encoding="utf-8"
    )
    (data / "human_review.csv").write_text(
        "question_id,annotator,reviewer,status\n"
        + "".join(q["id"] + ",fixture-author,fixture-reviewer,approved\n" for q in questions),
        encoding="utf-8",
    )
    manifest = read_json(data / "corpus_manifest.json")
    manifest.update(
        questions_sha256=sha256(data / "questions.jsonl"),
        human_review_sha256=sha256(data / "human_review.csv"),
    )
    (data / "corpus_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    mapping = read_json(root / "mapping.json")
    first = mapping["questions"][0]
    mapping["questions"] = [{**first, "id": q["id"]} for q in questions]
    mapping["parent_manifest_sha256"] = sha256(data / "corpus_manifest.json")
    (root / "mapping.json").write_text(json.dumps(mapping), encoding="utf-8")
    (root / "config.json").write_text(
        json.dumps(
            {
                "expected_test_queries": 30,
                "production_top_k": 5,
                "evaluation_top_k": 10,
                "concurrency": 1,
                "budget_usd": 0,
                "request_pacing": POLICY,
            }
        ),
        encoding="utf-8",
    )
    for name in (*EXTRA_FILES, *cont.FILES):
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# Synthetic controller fixture\n", encoding="utf-8")
    parent = root / ".cache/parent"
    prepare_parent(root, ".cache/parent", "data", "mapping.json", "config.json")
    protocol = read_json(parent / "protocol.json")
    execution = parent / "execution"
    execution.mkdir()
    grant = {
        "scope_id": "parent",
        "protocol_sha256": fingerprint(protocol),
        "total": request_bound(30),
        "batches": {q["id"]: request_bound(1) for q in questions},
    }
    write_json(execution / "grant.json", grant)
    ledger = RequestLedger.create(execution / "requests.sqlite", grant)
    ledger.bind_runtime("a" * 64)
    observed = []
    ref = capture["rows"][0]["retrieval"]["hits"]
    for q in questions[:8]:
        ledger.reserve(q["id"], "generateContent", q["id"])
        for _ in range(7):
            ledger.reserve(q["id"], "countTokens", q["id"])
        observed.append(observation(q["id"], ref))
    observed[-1] = {k: v for k, v in observed[-1].items() if k not in {"answer", "final_context"}}
    observed[-1].update(status="failed", error="provider")
    # A temporary metadata contract fixture; never published as actual native evidence.
    (execution / "capture").mkdir()
    write_json(
        execution / "capture/capture.json",
        {
            "schema": 1,
            "protocol_sha256": fingerprint(protocol),
            "origin": "captured_api",
            "split": "test",
            "rows": observed,
        },
    )
    write_json(
        execution / "summary.json",
        {
            "cleanup_completed": True,
            "queries": [{"id": r["id"]} for r in observed],
            "ledger": ledger.snapshot(),
        },
    )
    write_json(
        execution / "capture/execution.json",
        {
            "provider_kind": "native_gemini",
            "auth_override_present": False,
            "ledger": ledger.snapshot(),
        },
    )
    run_replay(
        root,
        parent / "protocol.json",
        execution / "capture/capture.json",
        execution / "evaluation",
        "test",
        allow_heldout=True,
    )
    output = root / ".cache/continuation"
    control = cont.prepare(root, ".cache/parent", ".cache/continuation")
    return root, parent, output, control, ledger, observation, ref


def test_prepare_preserves_parent_and_freezes_extension_separately(prepared):
    root, parent, output, control, *_ = prepared
    assert control["selected_ids"] == [f"q{i:03}" for i in range(9, 31)]
    assert read_json(output / "child-grant.json")["total"] == request_bound(22)
    assert read_json(output / "protocol.json") == read_json(parent / "protocol.json")
    assert not (output / "execution").exists()
    assert not (parent / "execution/continuation-01-claim.json").exists()
    cont.verify_control(root, output)


@pytest.mark.parametrize("change", ["pending", "quota", "free", "reference", "control"])
def test_approval_guard_before_runtime(prepared, monkeypatch, change):
    root, _, output, control, *_ = prepared
    approval = cont.approval_template(control)
    approval.update(
        state="approved",
        approval_reference="fixture",
        free_tier_confirmed=True,
        quota_confirmed=True,
    )
    key, value = {
        "pending": ("state", "pending"),
        "quota": ("quota_confirmed", False),
        "free": ("free_tier_confirmed", False),
        "reference": ("approval_reference", ""),
        "control": ("control_sha256", "0" * 64),
    }[change]
    approval[key] = value
    monkeypatch.setattr(cont, "native_capture", lambda *a: pytest.fail("No runtime"))
    with pytest.raises(ValueError, match="approval"):
        cont.execute(root, output, approval)
    assert not (output / "execution").exists()


@pytest.mark.parametrize("change", ["source", "archive", "evidence", "control"])
def test_source_and_historical_evidence_drift_refused(prepared, change):
    root, parent, output, control, *_ = prepared
    path = {
        "source": root / cont.FILES[0],
        "archive": output / "frozen-root" / cont.FILES[0],
        "evidence": parent / "execution/summary.json",
        "control": output / "control.json",
    }[change]
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        cont.verify_control(root, output, fingerprint(control))


def simulate_child(prepared):
    root, parent, output, control, original, observation, ref = prepared
    execution = output / "execution"
    execution.mkdir()
    grant = read_json(output / "child-grant.json")
    write_json(execution / "grant.json", grant)
    child = RequestLedger.create(execution / "requests.sqlite", grant)
    linked = cont.ContinuationLedger.claim(
        original,
        child,
        read_json(output / "parent-baseline.json"),
        parent / "execution/continuation-01-claim.json",
    )
    linked.bind_runtime("b" * 64)
    for q in control["selected_ids"]:
        linked.reserve(q, "countTokens", q)
        linked.reserve(q, "generateContent", q)
    (execution / "capture").mkdir()
    write_json(
        execution / "capture/capture.json",
        {
            "schema": 1,
            "protocol_sha256": control["protocol_sha256"],
            "origin": "captured_api",
            "split": "test",
            "rows": [observation(q, ref) for q in control["selected_ids"]],
        },
    )
    write_json(
        execution / "summary.json",
        {
            "cleanup_completed": True,
            "ledger": linked.snapshot(),
            "queries": [{"id": q} for q in control["selected_ids"]],
        },
    )
    run_replay(
        root,
        output / "protocol.json",
        execution / "capture/capture.json",
        execution / "evaluation",
        "test",
        allow_heldout=True,
    )


def test_composite_preserves_original_failure_and_unscored_review(prepared):
    root, parent, output, *_ = prepared
    before = sha256(parent / "execution/capture/capture.json")
    simulate_child(prepared)
    manifest, packet = cont.combine(root, output)
    assert manifest["status"] == "completed_with_errors"
    metrics = read_json(output / "composite/evaluation/metrics.json")
    assert (
        metrics["planned"],
        metrics["attempted"],
        metrics["succeeded"],
        metrics["technical_errors"],
        metrics["not_attempted"],
    ) == (30, 30, 29, 1, 0)
    assert packet == {"reviewable": 29, "planned": 30, "human_review": "pending"}
    assert sha256(parent / "execution/capture/capture.json") == before
    assert all(
        r["score"]["correctness"] is None for r in read_json(output / "review/reviewer-a.json")
    )


@pytest.mark.parametrize("change", ["repeat", "protocol", "capture-bytes", "ledger"])
def test_composite_rejects_replacement_and_drift(prepared, change):
    root, _, output, _, original, *_ = prepared
    simulate_child(prepared)
    capture_path = output / "execution/capture/capture.json"
    capture = read_json(capture_path)
    if change == "repeat":
        capture["rows"][0]["id"] = "q001"
    elif change == "protocol":
        capture["protocol_sha256"] = "0" * 64
    elif change == "capture-bytes":
        capture["rows"][0]["latency_ms"] += 1
    else:
        original.reserve("q009", "generateContent", "foreign-activity")
    if change != "ledger":
        capture_path.write_text(json.dumps(capture), encoding="utf-8")
    with pytest.raises(ValueError):
        cont.combine(root, output)
