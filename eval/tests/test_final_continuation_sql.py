"""Real SQL/Qdrant shared orchestration with a partially used parent and fake inference."""

import pytest

from eval import final_runner as runner
from eval.final_budget import RequestLedger, fingerprint, request_bound
from eval.final_continuation import ContinuationLedger, ledger_state
from eval.tests.test_final_runner_sql import (
    fixture_run,
    forbid_live_inference,
    no_tokenizer,
    parser_child_packages,
    verified_tls_context,
)

__all__ = [
    "fixture_run",
    "forbid_live_inference",
    "no_tokenizer",
    "parser_child_packages",
    "verified_tls_context",
]


@pytest.fixture
def continuation_env(fixture_run, monkeypatch):
    env = fixture_run
    original = runner.capture_run

    def capture(root, output, protocol, rows, old_unused_ledger, settings, profile, url, **kwargs):
        remaining = old_unused_ledger.grant["batches"]
        grant = {
            "scope_id": old_unused_ledger.grant["scope_id"],
            "protocol_sha256": fingerprint(protocol),
            "total": request_bound(3),
            "batches": {"already-failed": request_bound(1), **remaining},
        }
        env.parent = RequestLedger.create(root / "parent.sqlite", grant)
        env.parent.bind_runtime("a" * 64)
        env.parent.reserve("already-failed", "generateContent", "original-failure")
        for _ in range(7):
            env.parent.reserve("already-failed", "countTokens", "original-failure")
        env.baseline = ledger_state(env.parent)
        child_grant = {
            **old_unused_ledger.grant,
            "scope_id": grant["scope_id"] + "-continuation-01",
        }
        child = RequestLedger.create(output / "requests.sqlite", child_grant)
        env.ledger = ContinuationLedger.claim(env.parent, child, env.baseline, root / "claim.json")
        env.scope = fingerprint(child_grant)[:16]
        env.storage = root / "backend/.cache/final-capture" / env.scope
        env.collection = "final_" + env.scope
        return original(root, output, protocol, rows, env.ledger, settings, profile, url, **kwargs)

    monkeypatch.setattr(runner, "capture_run", capture)
    return env


@pytest.mark.parametrize("failure", [None, "budget", "timeout"])
def test_linked_parent_budget_capture_and_cleanup(continuation_env, failure):
    env = continuation_env
    env.failure = failure == "timeout"
    summary = env.execute(budget=0 if failure == "budget" else 2)
    assert summary["cleanup_completed"] and summary["native_http_events"] == []
    assert ledger_state(env.parent)["binding"] == env.baseline["binding"] == ["a" * 64]
    child = summary["ledger"]["total"]
    global_used = summary["ledger"]["global_allowance"]["total"]
    assert global_used == {
        "generateContent": 1 + child["generateContent"],
        "countTokens": 7 + child["countTokens"],
    }
    assert summary["ledger"]["global_allowance"]["batches"]["already-failed"] == request_bound(
        1
    ) | {
        "generateContent": 1,
    }
    if failure is None:
        assert [q["http_status"] for q in summary["queries"]] == [200, 200]
        # One source per synthetic question uses 3 counts, below the 7-count cap.
        assert child == {"countTokens": 6, "generateContent": 2}
    else:
        assert len(summary["queries"]) == 1
        assert summary["queries"][0]["http_status"] == (503 if failure == "budget" else 504)
        assert child["generateContent"] == (0 if failure == "budget" else 1)
