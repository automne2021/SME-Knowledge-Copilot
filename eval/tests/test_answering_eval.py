"""Oracle helper and fixture diagnostics without any live provider/DB calls."""

import hashlib
import json
import time
from pathlib import Path

import pytest

from app.core.errors import AppError
from eval.run_answering_eval import BudgetedProvider, count_call_bound, oracle_context, probes

CONFIG = Path(__file__).resolve().parents[1] / "configs/answering.json"


def test_synthetic_dev_protocol_is_bounded_and_does_not_read_holdout():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert config["test_queries_used"] == 0 and config["budget_usd"] == 0
    assert config["max_generation_calls"] == 10 and config["max_count_tokens_calls"] == 20
    assert len(config["cases"]) == 5
    for case in config["cases"]:
        if case["mode"] == "oracle":
            context = oracle_context(case)
            assert [row["excerpt"] for row in context] == case["evidence"]
            assert "evidence_id" not in context[0]  # assigned by production budget builder
    # The real Markdown fixture creates a standalone heading + body, plus support = 3 chunks.
    assert count_call_bound(config["cases"], 3, 5) == 21 > config["max_count_tokens_calls"]
    selected = [case for case in config["cases"] if case["id"] == "api_unknown"]
    assert count_call_bound(selected, 3, 5) == 5


def test_fixture_probes_are_diagnostics_not_accuracy():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    case = config["cases"][0]
    values = probes(
        case, {"answer_status": "grounded", "answer": "12 and 3", "citations": [{}, {}]}
    )
    assert all(values.values())
    assert not all(probes(case, {"answer": "unsupported"}).values())


def test_actual_fixture_chunk_count_detects_underestimated_request_budget(tmp_path):
    from app.core.config import get_settings
    from app.services.chunking import E5TokenCounter, split_document
    from app.services.parsing import parse_file

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    counter = E5TokenCounter(get_settings().hf_home / "hub")
    count = 0
    for name, text in config["api_documents"].items():
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        count += len(split_document(parse_file(path, path.suffix[1:]), counter))
    assert count == 3 > len(config["api_documents"])
    assert count_call_bound(config["cases"], count, 5) == 21


def test_run_wide_request_ledger_fails_closed_before_exceeding_budget(tmp_path):
    # Bypass provider construction: this test exercises only the local ledger.
    provider = object.__new__(BudgetedProvider)
    provider.config = {
        "max_generation_calls": 1,
        "max_count_tokens_calls": 1,
        "minimum_request_interval_seconds": 0,
    }
    provider.output, provider.sleep = tmp_path, lambda seconds: None
    provider.last_request = time.monotonic()
    provider.counts = {"generateContent": 0, "countTokens": 0}
    for action in provider.counts:
        provider.reserve(action)
        with pytest.raises(AppError) as exc:
            provider.reserve(action)
        assert exc.value.code == "eval_budget_exhausted"
    assert json.loads((tmp_path / "request_ledger.json").read_text()) == {
        "generateContent": 1,
        "countTokens": 1,
    }


def test_frozen_live_reports_keep_budget_failure_and_scoped_retest():
    reports = CONFIG.parent.parent / "reports"
    first = reports / "answering_dev_20261104T031918Z_fd3953b6"
    retest = reports / "answering_dev_20261104T032524Z_a2800bde"
    manifests, successes, source_sets = [], set(), []
    totals = {"generateContent": 0, "countTokens": 0}
    for path in (first, retest):
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        ledger = json.loads((path / "request_ledger.json").read_text(encoding="utf-8"))
        assert ledger == manifest["requests"]
        assert manifest["cleanup_completed"] and manifest["human_review"] == "pending"
        assert manifest["test_queries_used"] == 0
        # Historical runs hashed the input source, then pretty-serialized config.json.
        # Verify the actual input bytes AND semantic equivalence, preserve old artifacts.
        source_config = path / "source_snapshot/eval__configs__answering.json.txt"
        assert hashlib.sha256(source_config.read_bytes()).hexdigest() == manifest["config_sha256"]
        assert json.loads((path / "config.json").read_text(encoding="utf-8")) == json.loads(
            source_config.read_text(encoding="utf-8")
        )
        hashes = json.loads((path / "source_sha256.json").read_text(encoding="utf-8"))
        for name, expected in hashes.items():
            snapshot = (
                path / "source_snapshot" / (name.replace("\\", "/").replace("/", "__") + ".txt")
            )
            assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == expected
        source_sets.append(
            {key: value for key, value in hashes.items() if key.startswith("backend/")}
        )
        for line in (path / "per_question.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if not row.get("technical_error"):
                assert all(row["probes"].values())
                successes.add(row["id"])
        for key in totals:
            totals[key] += ledger[key]
        manifests.append(manifest)
    assert manifests[0]["status"] == "failed" and manifests[0]["technical_errors"] == 1
    assert manifests[0]["error_code"] == "eval_budget_exhausted"
    assert manifests[1]["status"] == "completed" and manifests[1]["technical_errors"] == 0
    execution = json.loads((retest / "execution.json").read_text(encoding="utf-8"))
    assert execution["selected_case_ids"] == ["api_unknown"]
    assert execution["max_count_tokens_calls"] == 5 and execution["max_generation_calls"] == 2
    assert source_sets[0] == source_sets[1]  # no backend/prompt change to obtain retest success
    assert len(successes) == 5 and totals == {"generateContent": 5, "countTokens": 25}
