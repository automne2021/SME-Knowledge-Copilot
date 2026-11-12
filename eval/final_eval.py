"""Offline freeze, captured-observation evaluation and human scoring; zero live calls.

Replay is explicitly labelled. It does not create a production API/browser capture,
verify billing, or replace final E2E acceptance. Importing this module is inert.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import unicodedata
import uuid
from datetime import UTC, datetime
from pathlib import Path

from eval.final_budget import fingerprint, request_bound
from eval.final_review import summarize, worksheet
from eval.span_metrics import aggregate, ranked_group_hits

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def inside(root, name):
    path = (Path(root) / name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("Path escapes frozen root")
    return path


def _git_state(root):
    def git(*args):
        result = subprocess.run(
            ["git", "--no-optional-locks", *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None

    return {"head": git("rev-parse", "HEAD"), "status_porcelain": git("status", "--porcelain")}


def freeze(
    root,
    dataset,
    mapping,
    config,
    output,
    source_paths=(),
    *,
    synthetic_smoke=False,
    synthetic_e2e=False,
):
    """Hash opaque questions without parsing them; no selection or model work."""
    root = Path(root).resolve()
    dataset, mapping, config = (inside(root, path) for path in (dataset, mapping, config))
    manifest_path = dataset / "corpus_manifest.json"
    manifest = read_json(manifest_path)
    if synthetic_smoke and synthetic_e2e:
        raise ValueError("Choose one synthetic protocol kind")
    dataset_kind = (
        "synthetic_browser_e2e"
        if synthetic_e2e
        else "synthetic_smoke"
        if synthetic_smoke
        else "human_reviewed"
    )
    if manifest.get("label_status") != dataset_kind:
        raise ValueError("A published human-reviewed dataset is required")
    expected = {
        "questions.jsonl": manifest["questions_sha256"],
        "source_blocks.json": manifest["source_blocks_sha256"],
        "human_review.csv": manifest["human_review_sha256"],
    }
    for entry in manifest["documents"] + manifest.get("fixtures", []):
        if entry["path"] in expected:
            raise ValueError("Duplicate dataset path")
        expected[entry["path"]] = entry["sha256"]
    paths = [manifest_path, mapping, config]
    for name, expected_hash in expected.items():
        path = inside(dataset, name)
        if sha256(path) != expected_hash:
            raise ValueError("Dataset checksum drift")
        paths.append(path)
    if read_json(mapping)["parent_manifest_sha256"] != sha256(manifest_path):
        raise ValueError("Mapping parent differs from frozen dataset")
    for name in source_paths:
        path = inside(root, name)
        relative = path.relative_to(root)
        if path.suffix != ".py" or relative.parts[0] not in {"backend", "eval"}:
            raise ValueError("Only explicit Python source is allowed in source fingerprints")
        paths.append(path)
    protocol = {
        "schema": 1,
        "dataset_kind": dataset_kind,
        "created_at": datetime.now(UTC).isoformat(),
        "dataset": dataset.relative_to(root).as_posix(),
        "mapping": mapping.relative_to(root).as_posix(),
        "config": config.relative_to(root).as_posix(),
        "files_sha256": {p.relative_to(root).as_posix(): sha256(p) for p in sorted(set(paths))},
        "source_file_count": len(set(source_paths)),
        "git": _git_state(root),
        "semantics": "offline-preparation-not-live-acceptance",
        "request_bound_30_top5_estimate": request_bound(30, 5),
    }
    write_json(output, protocol)
    return protocol


def verify(root, protocol):
    if protocol.get("schema") != 1 or not protocol.get("files_sha256"):
        raise ValueError("Invalid frozen protocol")
    for name, expected in protocol["files_sha256"].items():
        if sha256(inside(root, name)) != expected:
            raise ValueError("Frozen input/source changed")
    # Ensure key input paths are actually covered by the freeze.
    dataset = inside(root, protocol["dataset"])
    required = [protocol["mapping"], protocol["config"]] + [
        (dataset / name).relative_to(Path(root).resolve()).as_posix()
        for name in (
            "corpus_manifest.json",
            "questions.jsonl",
            "source_blocks.json",
            "human_review.csv",
        )
    ]
    if not set(required) <= set(protocol["files_sha256"]):
        raise ValueError("Incomplete frozen inputs")


def load_questions(root, protocol, split, allow_heldout=False):
    if split not in {"dev", "test"}:
        raise ValueError("Explicit dev/test split required")
    if split == "test" and not allow_heldout:
        raise ValueError("Held-out questions require explicit --allow-heldout after freeze")
    verify(root, protocol)
    dataset = inside(root, protocol["dataset"])
    questions = [
        json.loads(line)
        for line in (dataset / "questions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len({q["id"] for q in questions}) != len(questions):
        raise ValueError("Duplicate question ID")
    synthetic = protocol.get("dataset_kind") in {"synthetic_smoke", "synthetic_browser_e2e"}
    browser = protocol.get("dataset_kind") == "synthetic_browser_e2e"
    if synthetic and (
        split != "dev"
        or len(questions) != (6 if browser else 2)
        or any(q["split"] != "dev" for q in questions)
        or sorted(q["expected_abstain"] for q in questions)
        != ([False, False, True, True, True, True] if browser else [False, True])
        or read_json(dataset / "corpus_manifest.json").get("label_status")
        != protocol["dataset_kind"]
    ):
        raise ValueError(
            "Synthetic smoke is exactly two dev fixtures (browser six), never held-out"
        )
    reviews = list(
        csv.DictReader(io.StringIO((dataset / "human_review.csv").read_text(encoding="utf-8")))
    )
    if len(reviews) != len(questions) or len({r["question_id"] for r in reviews}) != len(reviews):
        raise ValueError("Dataset review identities differ")
    by_id = {row["question_id"]: row for row in reviews}
    families = {}
    for question in questions:
        review = by_id.get(question["id"], {})
        names = [review.get(key, "").strip().casefold() for key in ("annotator", "reviewer")]
        if synthetic and (review.get("status") != "synthetic_fixture" or any(names)):
            raise ValueError("Synthetic fixtures must not impersonate human review")
        if not synthetic and (
            review.get("status") != "approved" or not all(names) or names[0] == names[1]
        ):
            raise ValueError("Incomplete independent dataset review")
        if (
            question["split"] not in {"dev", "test"}
            or families.setdefault(question["family_id"], question["split"]) != question["split"]
        ):
            raise ValueError("Family split drift")
        if type(question["expected_abstain"]) is not bool or question["expected_abstain"] != (
            not question["gold_evidence"]
        ):
            raise ValueError("Answerability/gold mismatch")
    selected = [q for q in questions if q["split"] == split]
    if not selected:
        raise ValueError("Selected split is empty")
    return selected


def _block_key(document, block):
    return json.dumps([document, block], ensure_ascii=False)


def _normalize(text):
    # Same declared Unicode/soft-hyphen normalization as production parsing.normalize.
    return " ".join(unicodedata.normalize("NFC", text.replace("\u00ad", "-")).split())


def _gold(question, mapping):
    candidates = [q for q in mapping["questions"] if q["id"] == question["id"]]
    if len(candidates) != 1:
        raise ValueError("Missing/duplicate mapped question")
    evidence = candidates[0]["evidence"]
    if len(evidence) != len(question["gold_evidence"]):
        raise ValueError("Gold mapping drift")
    groups = {}
    for original, mapped in zip(question["gold_evidence"], evidence, strict=True):
        for key in ("evidence_id", "evidence_group_id", "document_id", "quote"):
            if original[key] != mapped[key]:
                raise ValueError("Gold evidence identity drift")
        document = mapped["document_id"]
        blocks = {b["block_id"]: b for b in mapping["documents"][document]["blocks"]}
        spans, parts = [], []
        for span in mapped["parser_spans"]:
            text = blocks[span["block_id"]]["normalized_text"]
            start, end = span["char_start"], span["char_end"]
            if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
                raise ValueError("Invalid mapped gold span")
            parts.append(text[start:end])
            spans.append({**span, "block_id": _block_key(document, span["block_id"])})
        if _normalize(" ".join(parts)) != _normalize(mapped["quote"]):
            raise ValueError("Mapped gold quote drift")
        groups.setdefault(mapped["evidence_group_id"], []).append(spans)
    return groups


def _chunk(reference, mapping):
    if not isinstance(reference, dict) or set(reference) != {
        "document_id",
        "chunk_index",
        "text_sha256",
    }:
        raise ValueError("Invalid canonical chunk reference")
    document = reference["document_id"]
    index = reference["chunk_index"]
    if document not in mapping["documents"] or type(index) is not int or index < 0:
        raise ValueError("Invalid document/chunk identity")
    chunks = mapping["documents"][document]["chunks"]
    if index >= len(chunks):
        raise ValueError("Chunk outside frozen mapping")
    chunk = chunks[index]
    if (
        reference["text_sha256"] != chunk["text_sha256"]
        or hashlib.sha256(chunk["text"].encode()).hexdigest() != chunk["text_sha256"]
    ):
        raise ValueError("Captured chunk text hash drift")
    return [
        {**span, "block_id": _block_key(document, span["block_id"])}
        for span in chunk["source_spans"]
    ]


def _latency(value):
    if type(value) not in {int, float} or not math.isfinite(value) or value < 0:
        raise ValueError("Missing/invalid captured latency")
    return value


def _answer(answer, context):
    # Structural sanity for the offline capture format, not semantic validation.
    if not isinstance(answer, dict) or set(answer) != {
        "answer_status",
        "claims",
        "limitations",
        "missing_information",
        "conflict_detected",
    }:
        raise ValueError("Capture requires the complete structured answer")
    status, claims = answer["answer_status"], answer["claims"]
    if status not in {"grounded", "partial", "insufficient_evidence"}:
        raise ValueError("Unknown answer status")
    if not isinstance(claims, list) or len(claims) > 12:
        raise ValueError("Invalid claims")
    if (status == "insufficient_evidence") != (len(claims) == 0):
        raise ValueError("Answer status/claims mismatch")
    for key in ("limitations", "missing_information"):
        if (
            not isinstance(answer[key], list)
            or len(answer[key]) > 5
            or any(
                not isinstance(text, str) or not 0 < len(text.strip()) <= 500
                for text in answer[key]
            )
        ):
            raise ValueError("Invalid answer limitations/missing information")
    conflict = answer["conflict_detected"]
    if type(conflict) is not bool or (status != "partial" and conflict):
        raise ValueError("Invalid conflict flag")
    if status == "grounded" and answer["missing_information"]:
        raise ValueError("Grounded answer cannot omit required information")
    if status == "partial" and not (answer["limitations"] or answer["missing_information"]):
        raise ValueError("Partial answer needs a stated limitation")
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {"text", "evidence_ids"}:
            raise ValueError("Invalid claim fields")
        refs = claim["evidence_ids"]
        if not isinstance(claim["text"], str) or not 0 < len(claim["text"].strip()) <= 1000:
            raise ValueError("Invalid claim text")
        if (
            not isinstance(refs, list)
            or not 1 <= len(refs) <= 10
            or any(not isinstance(ref, str) for ref in refs)
            or len(set(refs)) != len(refs)
            or not set(refs) <= set(context)
        ):
            raise ValueError("Invalid/unknown citation identity")
    if conflict and len({ref for claim in claims for ref in claim["evidence_ids"]}) < 2:
        raise ValueError("Conflict needs two evidence identities")


def evaluate_capture(root, protocol, capture, split, allow_heldout=False):
    if set(capture) != {"schema", "protocol_sha256", "origin", "split", "rows"}:
        raise ValueError("Unexpected capture fields; do not include credentials/provider bodies")
    if capture["schema"] != 1 or capture["protocol_sha256"] != fingerprint(protocol):
        raise ValueError("Capture protocol differs from freeze")
    if capture["origin"] not in {"offline_fixture", "captured_api"} or capture["split"] != split:
        raise ValueError("Explicit capture origin/split required")
    questions = load_questions(root, protocol, split, allow_heldout)
    mapping = read_json(inside(root, protocol["mapping"]))
    config = read_json(inside(root, protocol["config"]))
    if any(
        type(config.get(key)) is not int or not 1 <= config[key] <= 10
        for key in ("production_top_k", "evaluation_top_k")
    ) or (config["evaluation_top_k"] < config["production_top_k"]):
        raise ValueError("Invalid frozen retrieval limits")
    if not isinstance(capture["rows"], list):
        raise ValueError("Invalid capture rows")
    observations, selected = {}, {q["id"] for q in questions}
    for row in capture["rows"]:
        if row["id"] in observations or row["id"] not in selected:
            raise ValueError("Duplicate, foreign or wrong-split capture ID")
        observations[row["id"]] = row
    rows = []
    for question in questions:
        groups = _gold(question, mapping)
        row = {
            "id": question["id"],
            "expected_abstain": question["expected_abstain"],
            "required_groups": sorted(groups),
            "status": "not_attempted",
        }
        observed = observations.get(question["id"])
        if observed is not None:
            allowed = {
                "id",
                "status",
                "retrieval",
                "latency_ms",
                "answer",
                "final_context",
                "error",
            }
            if set(observed) - allowed or observed["status"] not in {"completed", "failed"}:
                raise ValueError("Invalid capture status/fields")
            row.update(status=observed["status"], latency_ms=_latency(observed["latency_ms"]))
            retrieval = observed["retrieval"]
            if set(retrieval) != {"status", "hits", "latency_ms"} or retrieval["status"] not in {
                "completed",
                "failed",
            }:
                raise ValueError("Invalid captured retrieval")
            hits = retrieval["hits"]
            if not isinstance(hits, list) or len(hits) > config["evaluation_top_k"]:
                raise ValueError("Captured retrieval exceeds top-k")
            identities = [fingerprint(hit) for hit in hits]
            if len(set(identities)) != len(identities):
                raise ValueError("Duplicate captured chunks")
            if retrieval["status"] == "failed" and hits:
                raise ValueError("Failed retrieval cannot contribute cached hits")
            ranks = ranked_group_hits(groups, [_chunk(hit, mapping) for hit in hits])
            row["retrieval"] = {
                "status": retrieval["status"],
                "hits": hits,
                "latency_ms": _latency(retrieval["latency_ms"]),
                "ranked_group_hits": [sorted(hit) for hit in ranks],
            }
            if row["status"] == "completed":
                if retrieval["status"] != "completed" or observed.get("error") is not None:
                    raise ValueError("Completed answer has a technical error")
                context = observed["final_context"]
                if not isinstance(context, list) or len(context) > config["production_top_k"]:
                    raise ValueError("Invalid final context")
                by_evidence, chosen = {}, set()
                for index, evidence in enumerate(context, 1):
                    if set(evidence) != {"evidence_id", "chunk"}:
                        raise ValueError("Invalid context fields")
                    evidence_id, ref = evidence["evidence_id"], evidence["chunk"]
                    if (
                        not isinstance(evidence_id, str)
                        or not re.fullmatch(r"E[1-9][0-9]?", evidence_id)
                        or evidence_id != f"E{index}"
                    ):
                        raise ValueError("Invalid evidence ID")
                    identity = fingerprint(ref)
                    if (
                        evidence_id in by_evidence
                        or identity in chosen
                        or identity not in identities[: config["production_top_k"]]
                    ):
                        raise ValueError("Context is not a unique subset of final retrieval hits")
                    _chunk(ref, mapping)
                    by_evidence[evidence_id] = ref
                    chosen.add(identity)
                _answer(observed["answer"], by_evidence)
                row.update(answer=observed["answer"], final_context=context)
            else:
                code = observed.get("error")
                if code not in {
                    "provider",
                    "timeout",
                    "retrieval",
                    "invalid_output",
                    "budget",
                    "other",
                }:
                    raise ValueError("Use a safe technical error category, not exception text")
                if observed.get("answer") is not None or observed.get("final_context") is not None:
                    raise ValueError("Failed answer cannot publish a cached draft")
                row["error"] = code
        rows.append(row)
    verify(root, protocol)
    return rows


def metrics(rows, reviews, run_id):
    retrieval_rows = [
        {
            "required_groups": row["required_groups"],
            "status": row.get("retrieval", {}).get("status", row["status"]),
            "ranked_group_hits": row.get("retrieval", {}).get("ranked_group_hits", []),
            "latency_ms": row.get("retrieval", {}).get("latency_ms", 0),
        }
        for row in rows
    ]
    attempted = [row for row in rows if row["status"] != "not_attempted"]
    errors = sum(row["status"] == "failed" for row in attempted)
    retrieval = aggregate(retrieval_rows)
    retrieval_errors = sum(row["status"] == "failed" for row in retrieval_rows)
    retrieval.update(
        technical_failures=retrieval_errors,
        technical_error_rate=retrieval_errors / len(attempted) if attempted else None,
        not_attempted=len(rows) - len(attempted),
    )
    latency = aggregate(
        [
            {"required_groups": [], "status": row["status"], "latency_ms": row["latency_ms"]}
            for row in attempted
        ]
    )["latency_ms"]
    return {
        "planned": len(rows),
        "attempted": len(attempted),
        "not_attempted": len(rows) - len(attempted),
        "succeeded": len(attempted) - errors,
        "technical_errors": errors,
        "technical_error_rate_attempted": errors / len(attempted) if attempted else None,
        "attempt_coverage": len(attempted) / len(rows) if rows else None,
        "captured_answer_latency_ms": latency,
        "retrieval": retrieval,
        "human": summarize(rows, reviews, run_id),
    }


def run_replay(root, protocol_path, capture_path, output, split, allow_heldout=False):
    protocol = read_json(protocol_path)
    capture_bytes = Path(capture_path).read_bytes()
    capture = json.loads(capture_bytes)
    rows = evaluate_capture(root, protocol, capture, split, allow_heldout)
    output = Path(output).resolve()
    # Reports must not mutate frozen inputs, even when a caller chooses a bad path.
    frozen_paths = [inside(root, name) for name in protocol["files_sha256"]]
    if output.is_relative_to(inside(root, protocol["dataset"])) or any(
        path.is_relative_to(output) for path in frozen_paths
    ):
        raise ValueError("Output overlaps frozen inputs")
    output.mkdir(parents=True, exist_ok=False)
    run_id = "offline_replay_" + uuid.uuid4().hex
    entries = worksheet(rows, run_id)
    scores = metrics(rows, entries, run_id)
    row_bytes = "".join(
        json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in rows
    ).encode("utf-8")
    manifest = {
        "schema": 1,
        "run_id": run_id,
        "execution_kind": "offline_replay",
        "dataset_kind": protocol.get("dataset_kind", "human_reviewed"),
        "origin": capture["origin"],
        "capture_provenance_independently_verified": False,
        "split": split,
        "protocol_sha256": fingerprint(protocol),
        "capture_sha256": hashlib.sha256(capture_bytes).hexdigest(),
        "per_question_sha256": hashlib.sha256(row_bytes).hexdigest(),
        "model_calls_this_run": 0,
        "cost_this_offline_run_usd": 0,
        "captured_provider_usage": None,
        "live_acceptance": "not_established_by_replay",
        "human_review": "pending",
        "status": (
            "incomplete"
            if scores["not_attempted"]
            else "completed_with_errors"
            if scores["technical_errors"]
            else "completed"
        ),
    }
    write_json(output / "manifest.json", manifest)
    write_json(output / "config.json", protocol)
    write_json(output / "metrics.json", scores)
    write_json(output / "human_review.json", entries)
    with (output / "per_question.jsonl").open("xb") as stream:
        stream.write(row_bytes)
    with (output / "capture.json").open("xb") as stream:
        stream.write(capture_bytes)
    with (output / "report.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            f"# Offline replay: {run_id}\n\nOrigin: `{capture['origin']}`; split: `{split}`.\n\n"
            f"Attempted {scores['attempted']}/{scores['planned']}; technical errors "
            f"{scores['technical_errors']}. Human review pending.\n\n"
            "No live API/browser/model execution. Captured latency is not replay runtime. "
            "This report does not close live E2E or held-out acceptance.\n"
        )
    return manifest


def rescore(report, review_path, output):
    report = Path(report)
    manifest = read_json(report / "manifest.json")
    if sha256(report / "per_question.jsonl") != manifest["per_question_sha256"]:
        raise ValueError("Published output rows changed")
    rows = [
        json.loads(line)
        for line in (report / "per_question.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    scores = metrics(rows, read_json(review_path), manifest["run_id"])
    write_json(
        output,
        {
            "run_id": manifest["run_id"],
            "review_sha256": sha256(review_path),
            "source_rows_sha256": sha256(report / "per_question.jsonl"),
            "execution_kind": "offline_human_rescore",
            "origin": manifest["origin"],
            "live_acceptance": manifest["live_acceptance"],
            "metrics": scores,
        },
    )
    return scores


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    frozen = sub.add_parser("freeze", help="Hash reviewed inputs without parsing questions")
    frozen.add_argument("--dataset", required=True)
    frozen.add_argument("--mapping", required=True)
    frozen.add_argument("--config", required=True)
    frozen.add_argument("--output", type=Path, required=True)
    replay = sub.add_parser("replay", help="Offline replay of explicit captures; no network")
    replay.add_argument("--protocol", type=Path, required=True)
    replay.add_argument("--capture", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    replay.add_argument("--split", choices=("dev", "test"), required=True)
    replay.add_argument("--allow-heldout", action="store_true")
    review = sub.add_parser("score", help="Validate a human worksheet and write a new metrics file")
    review.add_argument("--report", type=Path, required=True)
    review.add_argument("--reviews", type=Path, required=True)
    review.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze":
        sources = sorted(
            p.relative_to(ROOT).as_posix()
            for folder in (ROOT / "backend/app", ROOT / "eval")
            for p in folder.rglob("*.py")
        )
        result = freeze(ROOT, args.dataset, args.mapping, args.config, args.output, sources)
        print(json.dumps({"protocol_sha256": fingerprint(result), "questions_parsed": False}))
    elif args.command == "replay":
        result = run_replay(
            ROOT, args.protocol, args.capture, args.output, args.split, args.allow_heldout
        )
        print(json.dumps({key: result[key] for key in ("run_id", "execution_kind", "status")}))
    else:
        scores = rescore(args.report, args.reviews, args.output)
        print(
            json.dumps(
                {
                    "reviewed": scores["human"]["reviewed"],
                    "pending": scores["human"]["pending_or_disputed"],
                }
            )
        )


if __name__ == "__main__":
    main()
