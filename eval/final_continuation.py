"""One continuation of untouched held-out IDs; preserve original protocol and allowance."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from pathlib import Path

from eval.final_budget import RequestLedger, fingerprint, request_bound
from eval.final_eval import inside, read_json, run_replay, sha256, verify, write_json
from eval.final_runner import CANDIDATE, native_capture, verify_candidate
from eval.review_pack import build_pack, report_rows

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ".cache/final-heldout-continuation-20261112"
FILES = ("eval/final_continuation.py", "scripts/run-final-continuation.py")
EVIDENCE = (
    "execution/grant.json",
    "execution/summary.json",
    "execution/capture/capture.json",
    "execution/capture/execution.json",
    "execution/evaluation/manifest.json",
    "execution/evaluation/per_question.jsonl",
    "execution/evaluation/metrics.json",
)


def ledger_state(ledger):
    """Exact append-only baseline, including the parent's existing runtime binding."""
    with sqlite3.connect(ledger.path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        ledger._check(db)
        return {
            "grant": ledger.grant,
            "binding": [r[0] for r in db.execute("select plan_sha256 from runtime_binding")],
            "reservations": [
                list(r)
                for r in db.execute(
                    "select id,batch,action,query_id,reserved_at from reservations order by id"
                )
            ],
        }


def check_append_only(parent, baseline, batches, prefix):
    current = ledger_state(parent)
    if current["grant"] != baseline["grant"] or current["binding"] != baseline["binding"]:
        raise ValueError("Original grant/runtime binding changed")
    old = {r[0]: r for r in baseline["reservations"]}
    actual = {r[0]: r for r in current["reservations"]}
    if any(actual.get(key) != row for key, row in old.items()):
        raise ValueError("Original reservations were removed/changed")
    if any(
        r[1] not in batches or not r[3].startswith(prefix)
        for key, r in actual.items()
        if key not in old
    ):
        raise ValueError("Unexpected activity outside this continuation")


class ContinuationLedger:
    """Original allowance first, then child; no refund or parent binding reset."""

    def __init__(self, parent, child, baseline, claim_path, *, check=lambda: None):
        if (
            parent.path.resolve() == child.path.resolve()
            or child.grant["protocol_sha256"] != parent.grant["protocol_sha256"]
            or child.grant["scope_id"] != parent.grant["scope_id"] + "-continuation-01"
            or not set(child.grant["batches"]) <= set(parent.grant["batches"])
            or any(
                caps != parent.grant["batches"][batch]
                for batch, caps in child.grant["batches"].items()
            )
            or any(
                sum(c[a] for c in child.grant["batches"].values()) != limit
                for a, limit in child.grant["total"].items()
            )
        ):
            raise ValueError("Continuation cannot expand or replace the original allowance")
        if any(r[1] in child.grant["batches"] for r in baseline["reservations"]):
            raise ValueError("Only untouched batches may continue")
        self.parent, self.child, self.baseline = parent, child, baseline
        self.claim_path, self.check = Path(claim_path), check
        self.prefix = child.grant["scope_id"] + ":"
        self.claim = {
            "parent_grant_sha256": fingerprint(parent.grant),
            "baseline_sha256": fingerprint(baseline),
            "child_grant_sha256": fingerprint(child.grant),
        }
        if read_json(self.claim_path) != self.claim:
            raise ValueError("Continuation claim differs from frozen child/baseline")
        self.validate()

    @classmethod
    def claim(cls, parent, child, baseline, claim_path, **kwargs):
        if ledger_state(parent) != baseline:
            raise ValueError("Parent changed before continuation claim")
        write_json(
            claim_path,
            {
                "parent_grant_sha256": fingerprint(parent.grant),
                "baseline_sha256": fingerprint(baseline),
                "child_grant_sha256": fingerprint(child.grant),
            },
        )
        return cls(parent, child, baseline, claim_path, **kwargs)

    @property
    def grant(self):
        return self.child.grant

    def validate(self):
        self.check()
        if read_json(self.claim_path) != self.claim:
            raise ValueError("Continuation claim changed")
        check_append_only(self.parent, self.baseline, self.grant["batches"], self.prefix)

    def bind_runtime(self, digest):
        self.validate()
        return self.child.bind_runtime(digest)

    def reserve(self, batch, action, query_id):
        if batch not in self.grant["batches"] or action not in self.grant["total"]:
            raise ValueError("Batch/action outside continuation")
        self.validate()
        self.parent.reserve(batch, action, self.prefix + query_id)
        return self.child.reserve(batch, action, query_id)

    def snapshot(self):
        self.validate()
        return {**self.child.snapshot(), "global_allowance": self.parent.snapshot()}


def prepare(root, parent, output):
    root, parent, output = Path(root).resolve(), inside(root, parent), inside(root, output)
    if not output.is_relative_to(root / ".cache") or output.is_relative_to(parent):
        raise ValueError("Use a new separate .cache continuation directory")
    protocol, _ = verify_candidate(root, parent)
    manifest, rows = report_rows(parent / "execution/evaluation")
    summary = read_json(parent / "execution/summary.json")
    old_capture = read_json(parent / "execution/capture/capture.json")
    if (
        manifest["split"] != "test"
        or manifest["origin"] != "captured_api"
        or manifest["protocol_sha256"] != fingerprint(protocol)
        or manifest["capture_sha256"] != sha256(parent / "execution/capture/capture.json")
        or len(rows) != 30
        or not summary["cleanup_completed"]
        or [r["id"] for r in old_capture["rows"]] != [q["id"] for q in summary["queries"]]
    ):
        raise ValueError("Expected a cleaned native 30-question parent with exact output binding")
    untouched = [r["id"] for r in rows if r["status"] == "not_attempted"]
    if len(untouched) != 22 or set(untouched).intersection(r["id"] for r in old_capture["rows"]):
        raise ValueError("This continuation is exactly the 22 untouched questions")
    grant = read_json(parent / "execution/grant.json")
    if (
        grant["total"] != request_bound(30, 5)
        or set(grant["batches"]) != {r["id"] for r in rows}
        or any(c != request_bound(1, 5) for c in grant["batches"].values())
    ):
        raise ValueError("Original allowance differs from 60/210 fixed batches")
    runtime = read_json(parent / "execution/capture/execution.json")
    if (
        runtime["provider_kind"] != "native_gemini"
        or runtime["auth_override_present"]
        or runtime["ledger"] != summary["ledger"]
    ):
        raise ValueError("Parent must use native inference and real authentication")
    ledger = RequestLedger(parent / "execution/requests.sqlite", grant)
    baseline = ledger_state(ledger)
    if ledger.snapshot() != summary["ledger"] or len(baseline["binding"]) != 1:
        raise ValueError("Parent already changed or lacks its original runtime binding")
    child_grant = {
        "scope_id": grant["scope_id"] + "-continuation-01",
        "protocol_sha256": fingerprint(protocol),
        "total": request_bound(22, 5),
        "batches": {q: grant["batches"][q] for q in untouched},
    }
    if any(r[1] in untouched for r in baseline["reservations"]):
        raise ValueError("Selected question already has reservations")
    if any(
        ledger.snapshot()["total"][a] + cap > grant["total"][a]
        for a, cap in child_grant["total"].items()
    ):
        raise ValueError("Insufficient remaining original allowance")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(parent / "protocol.json", output / "protocol.json")
    write_json(output / "parent-baseline.json", baseline)
    write_json(output / "child-grant.json", child_grant)
    control = {
        "schema": 1,
        "parent": parent.relative_to(root).as_posix(),
        "protocol_sha256": fingerprint(protocol),
        "selected_ids": untouched,
        "child_grant_sha256": fingerprint(child_grant),
        "baseline_sha256": fingerprint(baseline),
        "parent_evidence_sha256": {n: sha256(parent / n) for n in EVIDENCE},
        "controller_files_sha256": {n: sha256(root / n) for n in FILES},
        "budget_usd": 0,
        "model_prompt_corpus_changed": False,
    }
    write_json(output / "control.json", control)
    write_json(output / "approval-template.json", approval_template(control))
    archive = output / "frozen-root"
    archive.mkdir()
    for name in {**protocol["files_sha256"], **control["controller_files_sha256"]}:
        target = archive / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(inside(root, name), target)
    shutil.copyfile(output / "protocol.json", archive / "protocol.json")
    verify_control(root, output)
    return control


def approval_template(control):
    return {
        "state": "pending",
        "approval_reference": None,
        "control_sha256": fingerprint(control),
        "budget_usd": 0,
        "free_tier_confirmed": False,
        "quota_confirmed": False,
    }


def verify_control(root, output, expected_sha256=None):
    root, output = Path(root).resolve(), Path(output).resolve()
    control, protocol = read_json(output / "control.json"), read_json(output / "protocol.json")
    if expected_sha256 is not None and fingerprint(control) != expected_sha256:
        raise ValueError("Continuation controller manifest changed after approval")
    parent = inside(root, control["parent"])
    if verify_candidate(root, parent)[0] != protocol:
        raise ValueError("Continuation must preserve the original protocol")
    verify(output / "frozen-root", protocol)
    if (
        fingerprint(protocol) != control["protocol_sha256"]
        or read_json(output / "frozen-root/protocol.json") != protocol
        or fingerprint(read_json(output / "parent-baseline.json")) != control["baseline_sha256"]
        or fingerprint(read_json(output / "child-grant.json")) != control["child_grant_sha256"]
        or set(control["controller_files_sha256"]) != set(FILES)
    ):
        raise ValueError("Continuation control/archive drift")
    for name, digest in control["controller_files_sha256"].items():
        if sha256(root / name) != digest or sha256(output / "frozen-root" / name) != digest:
            raise ValueError("Continuation source changed")
    for name, digest in control["parent_evidence_sha256"].items():
        if sha256(parent / name) != digest:
            raise ValueError("Original evidence changed")
    grant = read_json(output / "child-grant.json")
    if (
        list(grant["batches"]) != control["selected_ids"]
        or len(control["selected_ids"]) != 22
        or grant["total"] != request_bound(22, 5)
        or control["budget_usd"] != 0
    ):
        raise ValueError("Continuation selection/caps changed")
    return control, protocol


def execute(root, output, approval):
    root, output = Path(root).resolve(), Path(output).resolve()
    control, protocol = verify_control(root, output)
    if not isinstance(approval, dict):
        raise ValueError("Scoped approval must be an object")
    expected = approval_template(control)
    expected.update(
        state="approved",
        free_tier_confirmed=True,
        quota_confirmed=True,
        approval_reference=approval.get("approval_reference"),
    )
    if (
        approval != expected
        or not isinstance(expected["approval_reference"], str)
        or not (expected["approval_reference"].strip())
    ):
        raise ValueError("Separate scoped approval/free-tier/quota confirmation required")
    execution = output / "execution"
    if execution.exists():
        raise ValueError("One-shot continuation exists; never reset or retry")
    from app.core.config import Settings
    from eval.final_eval import load_questions
    from eval.run_capture_smoke import preflight

    settings = Settings(_env_file=root / ".env")
    # Read-only preflight includes local cache/config; no native request or inference.
    url, profile = preflight(settings)
    cfg = read_json(inside(root, protocol["config"]))
    from app.services.answering import PROMPT_VERSION

    fields = {
        "model": "embedding_model",
        "revision": "embedding_revision",
        "dimension": "embedding_dimension",
        "candidate_k": "retrieval_candidate_k",
        "production_top_k": "retrieval_top_k",
        "score_threshold": "retrieval_score_threshold",
    }
    fields.update(
        {
            k: k
            for k in cfg
            if k.startswith("llm_")
            or k in {"chunk_size_tokens", "chunk_overlap_tokens", "query_timeout_seconds"}
        }
    )
    if (
        any(getattr(settings, v) != cfg[k] for k, v in fields.items())
        or profile["index_version"] != cfg["expected_index_version"]
        or cfg["prompt_version"] != PROMPT_VERSION
    ):
        raise ValueError("Runtime differs from original frozen baseline")
    parent_path = inside(root, control["parent"]) / "execution"
    parent = RequestLedger(parent_path / "requests.sqlite", read_json(parent_path / "grant.json"))
    baseline = read_json(output / "parent-baseline.json")
    if ledger_state(parent) != baseline:
        raise ValueError("Parent changed before continuation execution")
    selected = set(control["selected_ids"])
    rows = [
        q for q in load_questions(root, protocol, "test", allow_heldout=True) if q["id"] in selected
    ]
    if [q["id"] for q in rows] != control["selected_ids"]:
        raise ValueError("Selected question order changed")
    execution.mkdir(exist_ok=False)
    grant = read_json(output / "child-grant.json")
    write_json(execution / "grant.json", grant)
    write_json(execution / "approval.json", approval)
    child = RequestLedger.create(execution / "requests.sqlite", grant)
    ledger = ContinuationLedger.claim(
        parent,
        child,
        baseline,
        parent_path / "continuation-01-claim.json",
        check=lambda: verify_control(root, output, fingerprint(control)),
    )
    return native_capture(root, execution, protocol, rows, ledger, settings, profile, url)


def combine(root, output):
    """Copy disjoint original observations; never replace an old success/failure."""
    root, output = Path(root).resolve(), Path(output).resolve()
    control, protocol = verify_control(root, output)
    parent = inside(root, control["parent"]) / "execution"
    child = output / "execution"
    old, new = (read_json(p / "capture/capture.json") for p in (parent, child))
    for capture in (old, new):
        if (
            capture["protocol_sha256"] != fingerprint(protocol)
            or capture["split"] != "test"
            or capture["origin"] != "captured_api"
        ):
            raise ValueError("Cannot combine different production protocols or fake observations")
    initial = {r["id"] for r in old["rows"]}
    ids = [r["id"] for r in new["rows"]]
    if (
        initial.intersection(ids)
        or len(ids) != len(set(ids))
        or not set(ids) <= set(control["selected_ids"])
    ):
        raise ValueError("Continuation repeats or replaces an original attempt")
    if not all(read_json(p / "summary.json")["cleanup_completed"] for p in (parent, child)):
        raise ValueError("Both scopes must be cleaned before aggregation")
    for path, capture in ((parent, old), (child, new)):
        manifest, _ = report_rows(path / "evaluation")
        if manifest["capture_sha256"] != sha256(path / "capture/capture.json"):
            raise ValueError("Published capture bytes changed")
        if [r["id"] for r in capture["rows"]] != [
            q["id"] for q in read_json(path / "summary.json")["queries"]
        ]:
            raise ValueError("Captured rows differ from query receipts")
    original = RequestLedger(parent / "requests.sqlite", read_json(parent / "grant.json"))
    linked = ContinuationLedger(
        original,
        RequestLedger(child / "requests.sqlite", read_json(child / "grant.json")),
        read_json(output / "parent-baseline.json"),
        parent / "continuation-01-claim.json",
        check=lambda: verify_control(root, output, fingerprint(control)),
    )
    if linked.snapshot() != read_json(child / "summary.json")["ledger"]:
        raise ValueError("Final child/global ledger differs from captured receipts")
    composite = output / "composite"
    composite.mkdir(exist_ok=False)
    merged = {**old, "rows": old["rows"] + new["rows"]}
    write_json(composite / "capture.json", merged)
    manifest = run_replay(
        root,
        output / "protocol.json",
        composite / "capture.json",
        composite / "evaluation",
        "test",
        allow_heldout=True,
    )
    write_json(
        composite / "provenance.json",
        {
            "kind": "two_session_composite_not_one_uninterrupted_run",
            "controller_sha256": fingerprint(control),
            "protocol_sha256": fingerprint(protocol),
            "sources": [
                {
                    "path": p.relative_to(root).as_posix(),
                    "capture_sha256": sha256(p / "capture/capture.json"),
                    "row_ids": [r["id"] for r in capture["rows"]],
                }
                for p, capture in ((parent, old), (child, new))
            ],
            "global_ledger": read_json(child / "summary.json")["ledger"]["global_allowance"],
            "original_failure_preserved": True,
        },
    )
    packet = build_pack(
        output / "frozen-root",
        output / "protocol.json",
        composite / "evaluation",
        output / "review",
        allow_heldout=True,
    )
    return manifest, packet


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify", "capture", "combine"))
    parser.add_argument("--parent", default=CANDIDATE)
    parser.add_argument("--output", default=OUTPUT)
    parser.add_argument("--approval", type=Path)
    args = parser.parse_args(argv)
    output = inside(ROOT, args.output)
    if args.command == "prepare":
        prepare(ROOT, args.parent, args.output)
        print("Continuation frozen;22 untouched IDs/caps44/154; no model calls")
    elif args.command == "verify":
        verify_control(ROOT, output)
        print("Original protocol and separate controller/archive/evidence verified")
    elif args.command == "capture":
        if not args.approval:
            raise ValueError("Scoped approval file required")
        execute(ROOT, output, read_json(args.approval))
    else:
        manifest, packet = combine(ROOT, output)
        print(json.dumps({"status": manifest["status"], "review": packet}))
    return 0
