"""Reproduce frozen dev metrics and verify source snapshots without rerunning a model."""

import hashlib
import json
from pathlib import Path

from eval.span_metrics import aggregate


def test_frozen_dev_run_preserves_denominator_sources_and_metrics():
    root = Path(__file__).resolve().parents[2]
    output = root / "eval/reports/retrieval_dev_20261103T101104Z_968416c5"
    report = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (output / "per_question.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    dev_ids = {
        q["id"]
        for line in (root / "eval/snapshots/reviewed-v1/questions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if (q := json.loads(line))["split"] == "dev"
    }
    assert {row["id"] for row in rows} == dev_ids and len(rows) == 15
    assert aggregate(rows) == report["metrics"]
    assert report["llm_calls"] == report["test_queries_used"] == 0
    assert report["cleanup_completed"] and report["mapping_drift_guard_verified"]
    hashes = json.loads((output / "source_sha256.json").read_text(encoding="utf-8"))
    for relative, expected in hashes.items():
        source = (
            output / "source_snapshot" / (relative.replace("\\", "/").replace("/", "__") + ".txt")
        )
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
