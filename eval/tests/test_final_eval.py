"""Offline preparation on temporary synthetic data only; never load reviewed holdout."""

import copy
import hashlib
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from eval.final_budget import (
    BudgetExceeded,
    GuardedProvider,
    LedgerUnavailable,
    RequestLedger,
    fingerprint,
    request_bound,
)
from eval.final_eval import (
    evaluate_capture,
    freeze,
    load_questions,
    metrics,
    read_json,
    rescore,
    run_replay,
    sha256,
    verify,
    write_json,
)
from eval.final_review import summarize, worksheet


@pytest.fixture(autouse=True)
def deny_network_and_project_corpus(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network calls in offline preparation tests")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    original_open = Path.open
    project_eval = Path(__file__).resolve().parents[1]

    def restricted_open(path, *args, **kwargs):
        resolved = path.resolve()
        if any(
            resolved.is_relative_to(project_eval / folder)
            for folder in ("snapshots", "datasets", "seeds", "reports", "mappings")
        ):
            raise AssertionError("Tests may use temporary synthetic data only")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", restricted_open)


@pytest.fixture
def frozen(tmp_path):
    dataset = tmp_path / "data"
    dataset.mkdir()
    questions, mapped = [], []
    text = "abcdefghij"
    span = {"block_id": "p1", "char_start": 0, "char_end": 10, "role": "content"}
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    documents = {}
    for doc in ("doc1", "doc2"):
        (dataset / f"{doc}.txt").write_text(text, encoding="utf-8")
        documents[doc] = {
            "sha256": sha256(dataset / f"{doc}.txt"),
            "blocks": [{"block_id": "p1", "normalized_text": text}],
            "chunks": [{"text": text, "text_sha256": text_hash, "source_spans": [span]}],
        }
    for index, (split, docs) in enumerate(
        [("dev", ["doc1"]), ("dev", ["doc1", "doc2"]), ("dev", []), ("test", ["doc2"])], 1
    ):
        question_id = f"fixture-{index}"
        evidence = [
            {
                "evidence_id": f"gold-{doc}",
                "evidence_group_id": doc,
                "document_id": doc,
                "quote": text,
            }
            for doc in docs
        ]
        questions.append(
            {
                "id": question_id,
                "split": split,
                "family_id": question_id,
                "question": "Synthetic fixture only",
                "expected_answer": text,
                "expected_abstain": not docs,
                "gold_evidence": evidence,
            }
        )
        mapped.append(
            {
                "id": question_id,
                "evidence": [{**entry, "parser_spans": [span]} for entry in evidence],
            }
        )
    (dataset / "questions.jsonl").write_text(
        "".join(json.dumps(q) + "\n" for q in questions), encoding="utf-8"
    )
    (dataset / "source_blocks.json").write_text("[]", encoding="utf-8")
    (dataset / "human_review.csv").write_text(
        "question_id,annotator,reviewer,status\n"
        + "".join(f"{q['id']},fixture-author,fixture-reviewer,approved\n" for q in questions),
        encoding="utf-8",
    )
    manifest = {
        "label_status": "human_reviewed",
        "questions_sha256": sha256(dataset / "questions.jsonl"),
        "source_blocks_sha256": sha256(dataset / "source_blocks.json"),
        "human_review_sha256": sha256(dataset / "human_review.csv"),
        "documents": [
            {"path": f"{doc}.txt", "sha256": value["sha256"]} for doc, value in documents.items()
        ],
        "fixtures": [],
    }
    write_json(dataset / "corpus_manifest.json", manifest)
    write_json(
        tmp_path / "mapping.json",
        {
            "parent_manifest_sha256": sha256(dataset / "corpus_manifest.json"),
            "questions": mapped,
            "documents": documents,
        },
    )
    write_json(tmp_path / "config.json", {"production_top_k": 5, "evaluation_top_k": 10})
    protocol_path = tmp_path / "protocol.json"
    protocol = freeze(tmp_path, "data", "mapping.json", "config.json", protocol_path)
    refs = [{"document_id": doc, "chunk_index": 0, "text_sha256": text_hash} for doc in documents]

    def observation(question_id, chosen, abstain=False):
        return {
            "id": question_id,
            "status": "completed",
            "latency_ms": 20,
            "retrieval": {"status": "completed", "hits": chosen, "latency_ms": 2},
            "final_context": [
                {"evidence_id": f"E{i}", "chunk": ref} for i, ref in enumerate(chosen, 1)
            ],
            "answer": {
                "answer_status": "insufficient_evidence" if abstain else "grounded",
                "claims": [] if abstain else [{"text": text, "evidence_ids": ["E1"]}],
                "limitations": [],
                "missing_information": [],
                "conflict_detected": False,
            },
        }

    capture = {
        "schema": 1,
        "protocol_sha256": fingerprint(protocol),
        "origin": "offline_fixture",
        "split": "dev",
        "rows": [
            observation("fixture-1", refs[:1]),
            observation("fixture-2", refs),
            observation("fixture-3", [], True),
        ],
    }
    return tmp_path, protocol_path, protocol, capture, refs, observation


def rows_for(frozen):
    root, _, protocol, capture, *_ = frozen
    return evaluate_capture(root, protocol, capture, "dev")


def approved(entry, row, correctness=2):
    entry = copy.deepcopy(entry)
    for index, review in enumerate(entry["reviews"]):
        review["reviewer"] = f"fixture-reviewer-{index}"
        review["score"]["correctness"] = correctness
        for claim in review["score"]["claims"]:
            claim["supported"] = True
            claim["citations"] = dict.fromkeys(claim["citations"], True)
    return entry


def grant(total=4, batch=2):
    return {
        "scope_id": "fixture-scope",
        "protocol_sha256": "a" * 64,
        "total": {"generateContent": total, "countTokens": total},
        "batches": {
            name: {"generateContent": batch, "countTokens": batch}
            for name in ("batch-1", "batch-2")
        },
    }


def test_freeze_hashes_questions_without_parsing_or_selecting(frozen):
    root, _, _, _, *_ = frozen
    path = root / "data/questions.jsonl"
    path.write_text("not JSON", encoding="utf-8")
    manifest = read_json(root / "data/corpus_manifest.json")
    manifest["questions_sha256"] = sha256(path)
    (root / "data/corpus_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    mapping = read_json(root / "mapping.json")
    mapping["parent_manifest_sha256"] = sha256(root / "data/corpus_manifest.json")
    (root / "mapping.json").write_text(json.dumps(mapping), encoding="utf-8")
    protocol = freeze(root, "data", "mapping.json", "config.json", root / "opaque.json")
    assert "files_sha256" in protocol


def test_explicit_holdout_guard_runs_before_question_file_is_opened(frozen, monkeypatch):
    root, _, protocol, *_ = frozen
    original = Path.open

    def denied(path, *args, **kwargs):
        if path.name == "questions.jsonl":
            raise AssertionError("Heldout content opened before consent")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(ValueError, match="allow-heldout"):
        load_questions(root, protocol, "test")


def test_only_explicitly_selected_fixture_split_is_scored(frozen):
    root, _, protocol, capture, refs, observation = frozen
    capture.update(split="test", rows=[observation("fixture-4", refs[1:])])
    rows = evaluate_capture(root, protocol, capture, "test", allow_heldout=True)
    assert [row["id"] for row in rows] == ["fixture-4"]
    with pytest.raises(ValueError, match="wrong-split"):
        evaluate_capture(root, protocol, {**capture, "split": "dev"}, "dev")


@pytest.mark.parametrize(
    "name", ["data/questions.jsonl", "data/doc1.txt", "mapping.json", "config.json"]
)
def test_frozen_input_drift_rejected_before_replay(frozen, name):
    root, _, protocol, *_ = frozen
    with (root / name).open("a", encoding="utf-8") as stream:
        stream.write(" ")
    with pytest.raises(ValueError, match="changed"):
        verify(root, protocol)


def test_missing_hash_and_path_escape_rejected(frozen):
    root, _, protocol, *_ = frozen
    protocol = copy.deepcopy(protocol)
    del protocol["files_sha256"]["data/questions.jsonl"]
    with pytest.raises(ValueError, match="Incomplete"):
        verify(root, protocol)
    protocol["files_sha256"]["../escaped"] = "a" * 64
    with pytest.raises(ValueError, match="escapes"):
        verify(root, protocol)


def test_chunk_identity_and_cross_document_block_namespace(frozen):
    rows = rows_for(frozen)
    result = metrics(rows, worksheet(rows, "run"), "run")
    assert result["retrieval"]["multi_evidence_successful"]["1"]["recall"] == 0.5
    assert result["retrieval"]["multi_evidence_successful"]["3"]["recall"] == 1
    assert result["human"]["correctness_mean_reviewed"] is None
    assert result["human"]["strict_success_rate"] is None


@pytest.mark.parametrize(
    "mutation", ["wrong-hash", "duplicate", "bad-citation", "unretrieved", "nan"]
)
def test_forged_capture_rejected(frozen, mutation):
    root, _, protocol, capture, refs, _ = frozen
    capture = copy.deepcopy(capture)
    first = capture["rows"][0]
    if mutation == "wrong-hash":
        first["retrieval"]["hits"][0]["text_sha256"] = "0" * 64
    elif mutation == "duplicate":
        capture["rows"].append(first)
    elif mutation == "bad-citation":
        first["answer"]["claims"][0]["evidence_ids"] = ["E99"]
    elif mutation == "unretrieved":
        first["final_context"][0]["chunk"] = refs[1]
    else:
        first["latency_ms"] = float("nan")
    with pytest.raises(ValueError):
        evaluate_capture(root, protocol, capture, "dev")


def test_partial_capture_keeps_planned_denominator_and_errors_are_not_abstentions(frozen):
    root, _, protocol, capture, *_ = frozen
    capture = copy.deepcopy(capture)
    capture["rows"] = [
        capture["rows"][0],
        {
            "id": "fixture-3",
            "status": "failed",
            "error": "timeout",
            "latency_ms": 150,
            "retrieval": {"status": "completed", "hits": [], "latency_ms": 2},
        },
    ]
    rows = evaluate_capture(root, protocol, capture, "dev")
    result = metrics(rows, worksheet(rows, "run"), "run")
    assert result["planned"] == 3 and result["attempted"] == 2
    assert result["not_attempted"] == 1 and result["technical_error_rate_attempted"] == 0.5
    assert result["human"]["abstention_sample_count"] == 1
    assert result["human"]["abstention_successful_only"]["recall"] is None
    assert result["retrieval"]["strict_all_answerable"]["5"]["recall"] == 0.5
    assert result["captured_answer_latency_ms"]["count"] == 1


def test_failed_retrieval_cannot_reuse_cached_hits(frozen):
    root, _, protocol, capture, *_ = frozen
    capture = copy.deepcopy(capture)
    capture["rows"][0]["status"] = "failed"
    capture["rows"][0]["retrieval"]["status"] = "failed"
    with pytest.raises(ValueError, match="cached hits"):
        evaluate_capture(root, protocol, capture, "dev")


def test_replay_artifacts_explicitly_identify_fixture_and_pending_quality(frozen):
    root, protocol_path, _, capture, *_ = frozen
    capture_path = root / "capture.json"
    write_json(capture_path, capture)
    output = root / "run"
    manifest = run_replay(root, protocol_path, capture_path, output, "dev")
    assert manifest["execution_kind"] == "offline_replay"
    assert manifest["origin"] == "offline_fixture" and manifest["model_calls_this_run"] == 0
    assert manifest["human_review"] == "pending"
    assert len(list(output.iterdir())) == 7
    with pytest.raises(FileExistsError):
        run_replay(root, protocol_path, capture_path, output, "dev")
    scores = rescore(output, output / "human_review.json", root / "rescored.json")
    assert scores["human"]["pending_or_disputed"] == 3
    assert read_json(output / "manifest.json") == manifest


def test_rescore_rejects_modified_published_rows(frozen):
    root, protocol_path, _, capture, *_ = frozen
    write_json(root / "capture.json", capture)
    report = root / "run"
    run_replay(root, protocol_path, root / "capture.json", report, "dev")
    with (report / "per_question.jsonl").open("a", encoding="utf-8") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="rows changed"):
        rescore(report, report / "human_review.json", root / "rescored.json")
    assert not (root / "rescored.json").exists()


def test_protocol_source_hashes_cover_uncommitted_code_and_reject_env_files(frozen):
    root, *_ = frozen
    (root / "eval").mkdir()
    source = root / "eval/local.py"
    source.write_text("VERSION = 1\n", encoding="utf-8")
    protocol = freeze(
        root, "data", "mapping.json", "config.json", root / "with-source.json", ["eval/local.py"]
    )
    source.write_text("VERSION = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        verify(root, protocol)
    with pytest.raises(ValueError, match="Python source"):
        freeze(root, "data", "mapping.json", "config.json", root / "bad-source.json", [".env"])
    assert not (root / "bad-source.json").exists()


def test_offline_cli_freeze_replay_and_score_use_fixture_root_only(frozen, monkeypatch, capsys):
    import eval.final_eval as cli

    root, _, _, capture, *_ = frozen
    monkeypatch.setattr(cli, "ROOT", root)
    protocol_path = root / "cli-protocol.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "final_eval",
            "freeze",
            "--dataset",
            "data",
            "--mapping",
            "mapping.json",
            "--config",
            "config.json",
            "--output",
            str(protocol_path),
        ],
    )
    cli.main()
    assert json.loads(capsys.readouterr().out)["questions_parsed"] is False
    capture["protocol_sha256"] = fingerprint(read_json(protocol_path))
    write_json(root / "cli-capture.json", capture)
    report = root / "cli-report"
    monkeypatch.setattr(
        "sys.argv",
        [
            "final_eval",
            "replay",
            "--protocol",
            str(protocol_path),
            "--capture",
            str(root / "cli-capture.json"),
            "--split",
            "dev",
            "--output",
            str(report),
        ],
    )
    cli.main()
    assert json.loads(capsys.readouterr().out)["execution_kind"] == "offline_replay"
    monkeypatch.setattr(
        "sys.argv",
        [
            "final_eval",
            "score",
            "--report",
            str(report),
            "--reviews",
            str(report / "human_review.json"),
            "--output",
            str(root / "cli-scored.json"),
        ],
    )
    cli.main()
    assert json.loads(capsys.readouterr().out) == {"reviewed": 0, "pending": 3}


def test_two_human_reviews_and_exact_output_binding(frozen):
    rows = rows_for(frozen)
    entries = [
        approved(entry, row) for entry, row in zip(worksheet(rows, "run"), rows, strict=True)
    ]
    result = summarize(rows, entries, "run")
    assert result["reviewed"] == 3 and result["strict_success_rate"] == 1
    assert result["faithfulness"] == 1 and result["citation_correctness"] == 1
    entries[0]["reviews"][1]["reviewer"] = " FIXTURE-REVIEWER-0 "
    with pytest.raises(ValueError, match="different people"):
        summarize(rows, entries, "run")
    entries[0]["reviews"][1]["reviewer"] = "fixture-reviewer-1"
    rows[0]["answer"]["claims"][0]["text"] = "Changed output"
    with pytest.raises(ValueError, match="exact output"):
        summarize(rows, entries, "run")


def test_disagreement_needs_explicit_adjudication_and_reviewer_agreement(frozen):
    rows = rows_for(frozen)
    entries = worksheet(rows, "run")
    entries[0] = approved(entries[0], rows[0])
    entries[0]["reviews"][1]["score"]["correctness"] = 1
    assert summarize(rows, entries, "run")["reviewed"] == 0
    entries[0]["adjudication"] = {
        "score": copy.deepcopy(entries[0]["reviews"][1]["score"]),
        "reason": "Fixture consensus after checking the source",
        "agreed_by": ["fixture-reviewer-0", "fixture-reviewer-1"],
    }
    assert summarize(rows, entries, "run")["correctness_mean_reviewed"] == 1
    entries[0]["adjudication"]["agreed_by"][1] = "unrelated-person"
    with pytest.raises(ValueError, match="original reviewers"):
        summarize(rows, entries, "run")


@pytest.mark.parametrize("bad_score", [True, -1, 3, 1.5])
def test_invalid_manual_scores_rejected(frozen, bad_score):
    rows = rows_for(frozen)
    entries = worksheet(rows, "run")
    entries[0]["reviews"][0]["score"]["correctness"] = bad_score
    with pytest.raises(ValueError, match="Correctness"):
        summarize(rows, entries, "run")


def test_empty_claim_denominators_remain_null(frozen):
    rows = [rows_for(frozen)[2]]
    entries = [approved(worksheet(rows, "run")[0], rows[0])]
    result = summarize(rows, entries, "run")
    assert result["faithfulness"] is None and result["citation_correctness"] is None
    assert result["citation_completeness"] is None


def test_grant_is_immutable_and_ledger_cannot_be_reset(tmp_path):
    path = tmp_path / "scope.sqlite"
    allowance = grant()
    ledger = RequestLedger.create(path, allowance)
    ledger.reserve("batch-1", "generateContent", "fixture-1")
    allowance["total"]["generateContent"] = 100
    with pytest.raises(ValueError, match="differs"):
        RequestLedger(path, allowance)
    with pytest.raises(FileExistsError):
        RequestLedger.create(path, grant())
    assert RequestLedger(path, grant()).snapshot()["total"]["generateContent"] == 1


def test_concurrent_reservations_and_restart_share_total_budget(tmp_path):
    path = tmp_path / "scope.sqlite"
    RequestLedger.create(path, grant())

    def attempt(index):
        ledger = RequestLedger(path, grant())
        try:
            ledger.reserve(f"batch-{index % 2 + 1}", "generateContent", f"fixture-{index}")
            return True
        except BudgetExceeded:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(attempt, range(24)))
    assert sum(outcomes) == 4
    assert RequestLedger(path, grant()).snapshot()["total"]["generateContent"] == 4


def test_lost_response_is_charged_and_exhaustion_never_calls_transport(tmp_path):
    ledger = RequestLedger.create(tmp_path / "scope.sqlite", grant(total=2, batch=1))
    events = []

    class Provider:
        def generate(self, payload, deadline):
            events.append("transport")
            raise TimeoutError("Fixture lost response")

    provider = GuardedProvider(Provider, ledger, "batch-1", "fixture-1")
    with pytest.raises(TimeoutError):
        provider.generate({}, 100)
    with pytest.raises(BudgetExceeded):
        provider.generate({}, 100)
    assert events == ["transport"] and ledger.snapshot()["total"]["generateContent"] == 1
    ledger.path.unlink()
    with pytest.raises(LedgerUnavailable):
        provider.generate({}, 100)
    assert events == ["transport"]


def test_count_and_generation_caps_independent_and_no_payloads_in_ledger(tmp_path):
    ledger = RequestLedger.create(tmp_path / "scope.sqlite", grant(total=2, batch=1))

    class Provider:
        def count_tokens(self, payload, deadline):
            return 42

        def generate(self, payload, deadline):
            return {"usage": None, "text": "fixture"}

    provider = GuardedProvider(Provider, ledger, "batch-1", "fixture-1")
    assert provider.count_tokens({"secret": "fixture-sensitive-marker"}, 100) == 42
    assert provider.generate({}, 100)["usage"] is None
    assert ledger.snapshot()["total"] == {"generateContent": 1, "countTokens": 1}
    assert b"fixture-sensitive-marker" not in ledger.path.read_bytes()
    assert request_bound(30, 5) == {"generateContent": 60, "countTokens": 210}


@pytest.mark.parametrize("invalid", [True, -1, 1.5])
def test_invalid_budget_caps_fail_before_creating_ledger(tmp_path, invalid):
    allowance = grant()
    allowance["total"]["generateContent"] = invalid
    path = tmp_path / "invalid.sqlite"
    with pytest.raises(ValueError):
        RequestLedger.create(path, allowance)
    assert not path.exists()
