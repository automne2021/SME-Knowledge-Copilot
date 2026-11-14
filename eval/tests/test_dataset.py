"""Regression checks for corrupted labels, split leakage and unsafe benchmark claims."""

import csv
import hashlib
import io
import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from eval.build_dataset import put
from eval.publish_reviewed import publish
from eval.validate_dataset import (
    QUESTION_SLICES,
    inspect_corpus,
    normalized,
    safe_path,
    validate,
    validate_questions,
)

DATASET = Path(__file__).resolve().parents[1] / "datasets"


@pytest.fixture
def labels():
    questions = [
        json.loads(line)
        for line in (DATASET / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    blocks = json.loads((DATASET / "source_blocks.json").read_text(encoding="utf-8"))
    docs = json.loads((DATASET / "corpus_manifest.json").read_text(encoding="utf-8"))["documents"]
    return questions, blocks, docs


def follow_up_history():
    return [
        {"role": "user", "content": "Quy định này áp dụng thế nào?"},
        {"role": "assistant", "content": "Quy định áp dụng theo điều kiện trong tài liệu."},
    ]


@pytest.fixture
def v2_labels(labels):
    questions, blocks, docs = labels
    for question in questions:
        question.update(
            dataset_version="v2",
            slice="text",
            split={"dev": "dev2", "test": "test2"}[question["split"]],
        )
    return questions, blocks, docs


def test_legacy_questions_and_explicit_v1_are_valid_without_mutation(labels):
    questions, blocks, docs = labels
    questions[0]["dataset_version"] = "v1"
    before = deepcopy(questions)
    validate_questions(questions, blocks, docs)
    assert questions == before


@pytest.mark.parametrize("slice_name", sorted(QUESTION_SLICES))
def test_v2_question_slices_are_valid_without_mutation(v2_labels, slice_name):
    questions, blocks, docs = v2_labels
    question = questions[0]
    question["slice"] = slice_name
    if slice_name == "follow_up":
        question["history"] = follow_up_history()
    before = deepcopy(questions)
    validate_questions(questions, blocks, docs)
    assert questions == before


def test_v1_and_v2_questions_can_coexist(labels):
    questions, blocks, docs = labels
    legacy = next(q for q in questions if q["expected_abstain"])
    v2 = questions[0]
    v2.update(dataset_version="v2", slice="text", split="dev2")
    validate_questions([legacy, v2], blocks, docs)


@pytest.mark.parametrize("version", [None, "v3", "draft-v1", 2, True, [], {}])
def test_reject_unknown_dataset_version(labels, version):
    questions, blocks, docs = labels
    questions[0]["dataset_version"] = version
    with pytest.raises(ValueError, match="Unknown dataset_version"):
        validate_questions(questions, blocks, docs)


@pytest.mark.parametrize("split", ["dev", "test", "DEV2", None, [], 2])
def test_v2_rejects_legacy_and_invalid_splits(v2_labels, split):
    questions, blocks, docs = v2_labels
    questions[0]["split"] = split
    with pytest.raises(ValueError, match="Invalid split for version"):
        validate_questions(questions, blocks, docs)


@pytest.mark.parametrize("split", ["dev2", "test2"])
def test_legacy_question_cannot_enter_v2_split(labels, split):
    questions, blocks, docs = labels
    questions[0]["split"] = split
    with pytest.raises(ValueError, match="Invalid split for version"):
        validate_questions(questions, blocks, docs)


def test_v2_requires_explicit_dataset_version(v2_labels):
    questions, blocks, docs = v2_labels
    del questions[0]["dataset_version"]
    with pytest.raises(ValueError, match="Invalid split for version"):
        validate_questions(questions, blocks, docs)


@pytest.mark.parametrize("slice_name", [None, "unknown", "", [], {}, 1])
def test_v2_rejects_unknown_slice(v2_labels, slice_name):
    questions, blocks, docs = v2_labels
    questions[0]["slice"] = slice_name
    with pytest.raises(ValueError, match="Unknown or missing slice"):
        validate_questions(questions, blocks, docs)


def test_v2_requires_slice(v2_labels):
    questions, blocks, docs = v2_labels
    del questions[0]["slice"]
    with pytest.raises(ValueError, match="Unknown or missing slice"):
        validate_questions(questions, blocks, docs)


def test_legacy_question_rejects_slice(labels):
    questions, blocks, docs = labels
    questions[0]["slice"] = "text"
    with pytest.raises(ValueError, match="slice requires dataset_version v2"):
        validate_questions(questions, blocks, docs)


@pytest.mark.parametrize("slice_name", sorted(QUESTION_SLICES - {"follow_up"}))
@pytest.mark.parametrize("history", [None, [], follow_up_history()])
def test_other_slices_reject_even_null_or_empty_history(v2_labels, slice_name, history):
    questions, blocks, docs = v2_labels
    questions[0].update(slice=slice_name, history=history)
    with pytest.raises(ValueError, match="history is only allowed for follow_up"):
        validate_questions(questions, blocks, docs)


def test_legacy_question_rejects_history(labels):
    questions, blocks, docs = labels
    questions[0]["history"] = follow_up_history()
    with pytest.raises(ValueError, match="history is only allowed for follow_up"):
        validate_questions(questions, blocks, docs)


def test_follow_up_requires_history(v2_labels):
    questions, blocks, docs = v2_labels
    questions[0]["slice"] = "follow_up"
    with pytest.raises(ValueError, match="follow_up requires non-empty history"):
        validate_questions(questions, blocks, docs)


@pytest.mark.parametrize("history", [None, [], "", "history", {}, False])
def test_follow_up_rejects_empty_or_non_list_history(v2_labels, history):
    questions, blocks, docs = v2_labels
    questions[0].update(slice="follow_up", history=history)
    with pytest.raises(ValueError, match="follow_up requires non-empty history"):
        validate_questions(questions, blocks, docs)


@pytest.mark.parametrize(
    ("turn", "message"),
    [
        (None, "exactly role and content"),
        ("assistant: text", "exactly role and content"),
        ({"content": "text"}, "exactly role and content"),
        ({"role": "assistant"}, "exactly role and content"),
        ({"role": "assistant", "content": "text", "extra": True}, "exactly role and content"),
        ({"role": "system", "content": "text"}, "History role"),
        ({"role": "tool", "content": "text"}, "History role"),
        ({"role": [], "content": "text"}, "History role"),
        ({"role": None, "content": "text"}, "History role"),
        ({"role": "assistant", "content": None}, "History content"),
        ({"role": "assistant", "content": 12}, "History content"),
        ({"role": "assistant", "content": []}, "History content"),
        ({"role": "assistant", "content": ""}, "History content"),
        ({"role": "assistant", "content": " \n\t"}, "History content"),
    ],
)
def test_follow_up_rejects_invalid_turn(v2_labels, turn, message):
    questions, blocks, docs = v2_labels
    questions[0].update(slice="follow_up", history=[turn, follow_up_history()[-1]])
    with pytest.raises(ValueError, match=message):
        validate_questions(questions, blocks, docs)


def test_history_must_end_with_assistant(v2_labels):
    questions, blocks, docs = v2_labels
    questions[0].update(slice="follow_up", history=follow_up_history()[:1])
    with pytest.raises(ValueError, match="History must end with assistant"):
        validate_questions(questions, blocks, docs)


def test_v2_still_checks_gold_spans(v2_labels):
    questions, blocks, docs = v2_labels
    questions[0]["gold_evidence"][0]["quote"] = "fabricated"
    with pytest.raises(ValueError, match="Quote/source span mismatch"):
        validate_questions(questions, blocks, docs)


@pytest.mark.parametrize("same_family", [True, False])
def test_v2_rejects_family_or_source_split_leak(v2_labels, same_family):
    questions, blocks, docs = v2_labels
    first = questions[0]
    other = deepcopy(first)
    other.update(id="v2-other", split="test2")
    if not same_family:
        other["family_id"] = "different-family"
    message = "Family leaks" if same_family else "source block leaks"
    with pytest.raises(ValueError, match=message):
        validate_questions([first, other], blocks, docs)


def test_v1_held_out_evidence_cannot_be_relabelled_as_dev2(labels):
    questions, blocks, docs = labels
    held_out = next(q for q in questions if q["split"] == "test" and q["gold_evidence"])
    v2 = deepcopy(held_out)
    v2.update(
        id="v2-new", family_id="v2-new-family", dataset_version="v2", slice="text", split="dev2"
    )
    with pytest.raises(ValueError, match="source block leaks"):
        validate_questions([held_out, v2], blocks, docs)


def write_test_questions(root, manifest, questions):
    """Rehash controlled temporary labels, never the draft or reviewed snapshot."""
    path = root / "questions.jsonl"
    path.write_text(
        "".join(json.dumps(q, ensure_ascii=False) + "\n" for q in questions), encoding="utf-8"
    )
    manifest.update(
        questions_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        question_count=len(questions),
    )
    (root / "corpus_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


@pytest.fixture
def v2_package(tmp_path, labels):
    """Synthetic schema fixture: reused text, not the future v2 corpus or quality labels."""
    root = tmp_path / "v2"
    shutil.copytree(DATASET, root, ignore=shutil.ignore_patterns("~$*"))
    originals, _, _ = labels
    questions = []
    unanswerable = [q for q in originals if q["expected_abstain"]]
    for slice_name in sorted(QUESTION_SLICES):
        minimum = 6 if slice_name in {"scan", "follow_up"} else 8
        for _ in range(minimum):
            pool = unanswerable if slice_name == "unanswerable" else originals
            question = deepcopy(pool[len(questions) % len(pool)])
            question.update(
                id=f"v2-{len(questions):03}",
                dataset_version="v2",
                slice=slice_name,
                split={"dev": "dev2", "test": "test2"}[question["split"]],
            )
            if slice_name == "follow_up":
                question["history"] = follow_up_history()
            questions.append(question)
    manifest = json.loads((root / "corpus_manifest.json").read_text(encoding="utf-8"))
    # Four real temporary text files exercise the v2 package bounds, with no gold facts.
    for index in range(4):
        path = root / "corpus" / f"schema-extra-{index}.txt"
        path.write_text("Synthetic schema fixture only.", encoding="utf-8")
        manifest["documents"].append(
            {
                "document_id": f"schema-extra-{index}",
                "version": 1,
                "path": path.relative_to(root).as_posix(),
                "format": "txt",
                "block_count": 0,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    manifest.update(schema_version=2, dataset_version="schema-fixture-v2")
    write_test_questions(root, manifest, questions)
    with (root / "human_review.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["question_id", "split", "status", "annotator", "reviewer", "notes"])
        writer.writerows([q["id"], q["split"], "pending", "", "", ""] for q in questions)
    return root, manifest, questions


def test_validate_v2_package_and_review_gate(v2_package):
    root, _, _ = v2_package
    result = validate(root)
    assert result["documents"] == 14 and result["questions"] == 68
    assert result["dataset_versions"] == {"v2": 68}
    assert set(result["slices"]) == QUESTION_SLICES
    assert result["human_approved"] == 0 and result["model_benchmark"] == "not_run"
    with pytest.raises(ValueError, match="human review is incomplete"):
        validate(root, require_reviewed=True)


def test_validate_v2_package_rejects_too_few_questions(v2_package):
    root, manifest, questions = v2_package
    write_test_questions(root, manifest, questions[:59])
    with pytest.raises(ValueError, match="Question count for v2"):
        validate(root)


def test_validate_v2_package_requires_slice_coverage(v2_package):
    root, manifest, questions = v2_package
    next(q for q in questions if q["slice"] == "text")["slice"] = "identifier"
    write_test_questions(root, manifest, questions)
    with pytest.raises(ValueError, match="Slice coverage: text"):
        validate(root)


def test_validate_v2_package_does_not_use_v1_document_bounds(v2_package):
    root, manifest, _ = v2_package
    manifest["documents"].pop()
    (root / "corpus_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Expected 14–24 documents for v2"):
        validate(root)


def test_draft_requires_independent_review(tmp_path):
    root = tmp_path / "draft"
    shutil.copytree(DATASET, root, ignore=shutil.ignore_patterns("~$*"))
    path = root / "human_review.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    for row in rows:
        row.update(status="pending", annotator="", reviewer="")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = validate(root)
    assert (result["documents"], result["fixtures"], result["questions"]) == (10, 8, 45)
    assert result["splits"] == {"dev": 15, "test": 30}
    assert result["unanswerable"] == 6
    assert result["human_approved"] == 0
    assert result["label_status"] == "draft_pending_independent_human_review"
    assert result["model_benchmark"] == "not_run"
    with pytest.raises(ValueError, match="human review is incomplete"):
        validate(root, require_reviewed=True)


def test_publish_requires_complete_review_and_preserves_source(tmp_path):
    source = tmp_path / "draft"
    shutil.copytree(DATASET, source, ignore=shutil.ignore_patterns("~$*"))
    # Controlled synthetic reviewer identities for the publication contract test.
    path = source / "human_review.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    for row in rows:
        row.update(status="approved", annotator="Test A", reviewer="Test B")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    before = (source / "corpus_manifest.json").read_bytes()
    output = tmp_path / "reviewed"
    assert publish(source, output)["human_approved"] == 45
    assert (source / "corpus_manifest.json").read_bytes() == before
    frozen = (output / "corpus_manifest.json").read_bytes()
    publish(source, output)
    assert (output / "corpus_manifest.json").read_bytes() == frozen
    with path.open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ValueError, match="Existing reviewed snapshot differs"):
        publish(source, output)
    assert (output / "corpus_manifest.json").read_bytes() == frozen
    with (output / "human_review.csv").open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ValueError, match="Frozen human review checksum"):
        validate(output, require_reviewed=True)


def test_publish_rejects_pending_review_before_creating_output(tmp_path):
    source = tmp_path / "draft"
    shutil.copytree(DATASET, source, ignore=shutil.ignore_patterns("~$*"))
    path = source / "human_review.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    rows[0]["status"] = "pending"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    output = tmp_path / "reviewed"
    with pytest.raises(ValueError, match="Human review is incomplete"):
        publish(source, output)
    assert not output.exists()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("quote", "fabricated quote", "Quote/source span"),
        ("char_end", 99999, "Invalid source span"),
        ("char_start", True, "Offsets must be integers"),
        ("document_version", 999, "Revision mismatch"),
        ("document_id", "security", "Document/block mismatch"),
        ("source_block_id", "missing", "Unknown canonical source block"),
        ("evidence_group_id", "wrong-group", "Evidence group/block"),
        ("location", {"kind": "pdf_page", "page_start": 99}, "Evidence location"),
    ],
)
def test_reject_corrupted_evidence(labels, field, value, message):
    questions, blocks, docs = labels
    questions[0]["gold_evidence"][0][field] = value
    with pytest.raises(ValueError, match=message):
        validate_questions(questions, blocks, docs)


def test_reject_duplicate_question_id(labels):
    questions, blocks, docs = labels
    questions[1]["id"] = questions[0]["id"]
    with pytest.raises(ValueError, match="Duplicate question ID"):
        validate_questions(questions, blocks, docs)


def test_reject_family_split_leak(labels):
    questions, blocks, docs = labels
    questions[15]["family_id"] = questions[0]["family_id"]
    with pytest.raises(ValueError, match="Family leaks"):
        validate_questions(questions, blocks, docs)


def test_reject_source_split_leak_even_with_different_family(labels):
    questions, blocks, docs = labels
    questions[15]["gold_evidence"] = questions[0]["gold_evidence"]
    with pytest.raises(ValueError, match="source block leaks"):
        validate_questions(questions, blocks, docs)


def test_reject_answerable_question_without_evidence(labels):
    questions, blocks, docs = labels
    questions[0]["gold_evidence"] = []
    with pytest.raises(ValueError, match="Answerability/evidence"):
        validate_questions(questions, blocks, docs)


def test_reject_changed_corpus_checksum(tmp_path):
    root = tmp_path / "dataset"
    shutil.copytree(DATASET, root)
    manifest = json.loads((root / "corpus_manifest.json").read_text(encoding="utf-8"))
    with (root / manifest["documents"][0]["path"]).open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="Artifact checksum"):
        validate(root)


def test_reject_changed_label_checksum(tmp_path):
    root = tmp_path / "dataset"
    shutil.copytree(DATASET, root)
    with (root / "questions.jsonl").open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ValueError, match="Label checksum"):
        validate(root)


@pytest.mark.parametrize(
    ("annotator", "reviewer", "message"),
    [
        ("", "Person B", "needs human annotator"),
        ("Person A", "", "needs independent reviewer"),
        ("Person A", " person a ", "must be different people"),
    ],
)
def test_reject_review_without_two_distinct_people(tmp_path, annotator, reviewer, message):
    root = tmp_path / "dataset"
    shutil.copytree(DATASET, root)
    path = root / "human_review.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    rows[0]["status"] = "approved"
    rows[0]["annotator"] = annotator
    rows[0]["reviewer"] = reviewer
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match=message):
        validate(root)


def test_docx_locations_do_not_invent_pages(labels):
    _, blocks, docs = labels
    block = next(b for b in blocks if b["document_id"] == "leave")
    block["location"]["page_start"] = 1
    with pytest.raises(ValueError, match="fake page"):
        inspect_corpus(DATASET, docs, blocks)


def test_pdf_evidence_must_be_on_actual_cited_page(labels):
    _, blocks, docs = labels
    block = next(
        b for b in blocks if b["document_id"] == "acceptance" and b["location"]["page_start"] == 2
    )
    block["location"]["page_start"] = 1
    with pytest.raises(ValueError, match="PDF quote not on cited page"):
        inspect_corpus(DATASET, docs, blocks)


def test_pdf_comparison_normalizes_soft_hyphen_and_unicode():
    assert normalized("BM\u00ad09\nnghie\u0302\u0323m thu") == "BM-09 nghiệm thu"


def test_artifact_paths_cannot_escape_root(tmp_path):
    with pytest.raises(ValueError, match="escapes dataset root"):
        safe_path(tmp_path / "dataset", "../private.txt")


def test_builder_never_overwrites_edited_artifacts(tmp_path):
    path = tmp_path / "reviewed.txt"
    put(path, b"original")
    put(path, b"original")
    with pytest.raises(ValueError, match="Artifact differs"):
        put(path, b"replacement")
    assert path.read_bytes() == b"original"
