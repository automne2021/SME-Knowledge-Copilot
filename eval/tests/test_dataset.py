"""Regression checks for corrupted labels, split leakage and unsafe benchmark claims."""

import csv
import io
import json
import shutil
from pathlib import Path

import pytest

from eval.build_dataset import put
from eval.validate_dataset import (
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


def test_frozen_dataset_is_structurally_valid_but_not_human_reviewed():
    result = validate(DATASET)
    assert (result["documents"], result["fixtures"], result["questions"]) == (10, 8, 45)
    assert result["splits"] == {"dev": 15, "test": 30}
    assert result["unanswerable"] == 6
    assert result["human_approved"] == 0
    assert result["label_status"] == "draft_pending_independent_human_review"
    assert result["model_benchmark"] == "not_run"
    with pytest.raises(ValueError, match="human review is incomplete"):
        validate(DATASET, require_reviewed=True)


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
