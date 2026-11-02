"""Validate frozen synthetic artifacts and draft evidence; no inference or DB writes."""

import argparse
import csv
import hashlib
import json
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

QUESTION_TYPES = {
    "direct_fact",
    "paraphrase",
    "multi_section",
    "conditional",
    "exact_identifier",
    "cross_document",
    "conflict",
    "unanswerable",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), "Artifact path escapes dataset root")
    return path


def normalized(text: str) -> str:
    # PyMuPDF may expose a line-wrapped hyphen as U+00AD (e.g. BM-09).
    # This is a declared comparison normalization, not a parser span remap.
    return " ".join(unicodedata.normalize("NFC", text).replace("\u00ad", "-").split())


def validate_questions(questions: list[dict], blocks: list[dict], documents: list[dict]) -> None:
    ids = [q["id"] for q in questions]
    require(len(ids) == len(set(ids)), "Duplicate question ID")
    by_block = {b["source_block_id"]: b for b in blocks}
    require(len(by_block) == len(blocks), "Duplicate canonical source block")
    by_document = {d["document_id"]: d for d in documents}
    require(len(by_document) == len(documents), "Duplicate document ID")
    families, evidence_splits = {}, {}
    for q in questions:
        require(q["split"] in {"dev", "test"}, "Invalid split")
        require(q["question_type"] in QUESTION_TYPES, "Unknown question type")
        require(bool(q["question"].strip()) and bool(q["expected_answer"].strip()), "Empty Q/A")
        family = q["family_id"]
        require(bool(family.strip()), "Empty question family")
        require(families.setdefault(family, q["split"]) == q["split"], "Family leaks across splits")
        evidence = q["gold_evidence"]
        require(type(q["expected_abstain"]) is bool, "Abstain must be boolean")
        require(q["expected_abstain"] == (len(evidence) == 0), "Answerability/evidence mismatch")
        require(
            q["expected_abstain"] == (q["question_type"] == "unanswerable"),
            "Unanswerable question type mismatch",
        )
        expected_status = q["expected_answer_status"]
        require(expected_status in {"grounded", "partial", "insufficient_evidence"}, "Bad status")
        require(
            (expected_status == "insufficient_evidence") == q["expected_abstain"],
            "Bad status/evidence",
        )
        evidence_ids = [e["evidence_id"] for e in evidence]
        require(len(evidence_ids) == len(set(evidence_ids)), "Duplicate evidence ID in question")
        for item in evidence:
            block = by_block.get(item["source_block_id"])
            require(block is not None, "Unknown canonical source block")
            require(item["evidence_group_id"] == block["ref"], "Evidence group/block mismatch")
            doc = by_document.get(item["document_id"])
            require(doc is not None, "Unknown evidence document")
            require(item["document_id"] == block["document_id"], "Document/block mismatch")
            require(
                item["document_version"] == doc["version"] == block["document_version"],
                "Revision mismatch",
            )
            start, end = item["char_start"], item["char_end"]
            require(type(start) is int and type(end) is int, "Offsets must be integers")
            require(0 <= start < end <= len(block["text"]), "Invalid source span")
            require(block["text"][start:end] == item["quote"], "Quote/source span mismatch")
            require(item["location"] == block["location"], "Evidence location mismatch")
            require(
                evidence_splits.setdefault(item["source_block_id"], q["split"]) == q["split"],
                "Gold source block leaks across splits",
            )


def inspect_corpus(root: Path, documents: list[dict], blocks: list[dict]) -> None:
    import pymupdf
    from docx import Document

    for doc in documents:
        path = safe_path(root, doc["path"])
        relevant = [b for b in blocks if b["document_id"] == doc["document_id"]]
        require(len(relevant) == doc["block_count"], "Document block count mismatch")
        if doc["format"] == "pdf":
            with pymupdf.open(path) as pdf:
                require(not pdf.needs_pass, "Corpus PDF unexpectedly encrypted")
                for block in relevant:
                    loc = block["location"]
                    require(loc["kind"] == "pdf_page", "PDF location kind mismatch")
                    page = loc["page_start"]
                    require(1 <= page <= pdf.page_count, "PDF page outside source")
                    require(
                        normalized(block["text"]) in normalized(pdf[page - 1].get_text()),
                        f"PDF quote not on cited page: {block['source_block_id']}",
                    )
        elif doc["format"] == "docx":
            paragraphs = Document(path).paragraphs
            for block in relevant:
                loc = block["location"]
                require(loc["kind"] == "docx_block", "DOCX cannot have invented page numbers")
                require("page_start" not in loc, "DOCX contains fake page")
                require(
                    normalized(paragraphs[loc["block_start"] - 1].text) == block["text"],
                    "DOCX block mismatch",
                )
        else:
            require(doc["format"] in {"txt", "md"}, "Unsupported corpus format")
            lines = path.read_text(encoding="utf-8").splitlines()
            for block in relevant:
                loc = block["location"]
                require(loc["kind"] == "line_range", "Text location kind mismatch")
                require(lines[loc["line_start"] - 1] == block["text"], "Text line mismatch")


def inspect_fixtures(root: Path) -> None:
    import pymupdf

    with pymupdf.open(root / "fixtures/scan.pdf") as pdf:
        require(not any(p.get_text().strip() for p in pdf), "Scan fixture has a text layer")
        require(bool(pdf[0].get_images()), "Scan fixture has no image")
    with pymupdf.open(root / "fixtures/blank.pdf") as pdf:
        require(
            not pdf[0].get_text().strip() and not pdf[0].get_images(), "Blank fixture not blank"
        )
    with pymupdf.open(root / "fixtures/mixed.pdf") as pdf:
        require(pdf.page_count == 2, "Mixed fixture page count")
        require(bool(pdf[0].get_text().strip()), "Mixed text page missing text")
        require(
            not pdf[1].get_text().strip() and bool(pdf[1].get_images()), "Mixed scan page invalid"
        )
    with pymupdf.open(root / "fixtures/encrypted.pdf") as pdf:
        require(bool(pdf.needs_pass), "Encrypted fixture does not require password")
    try:
        with pymupdf.open(root / "fixtures/malformed.pdf"):
            pass
    except pymupdf.FileDataError:
        pass
    else:
        raise ValueError("Malformed PDF unexpectedly opens")
    require(
        not (root / "fixtures/spoofed.pdf").read_bytes().startswith(b"%PDF"),
        "Spoofed PDF has signature",
    )
    require(not zipfile.is_zipfile(root / "fixtures/malformed.docx"), "Malformed DOCX is a ZIP")
    require(
        (root / "fixtures/prompt_injection.txt")
        .read_text(encoding="utf-8")
        .startswith("[UNTRUSTED TEST DATA]"),
        "Adversarial fixture marker missing",
    )


def validate(root: Path, require_reviewed: bool = False) -> dict:
    manifest = json.loads((root / "corpus_manifest.json").read_text(encoding="utf-8"))
    require(manifest["synthetic"] is True, "Corpus provenance must be synthetic")
    require(
        manifest["label_status"] in {"draft_pending_independent_human_review", "human_reviewed"},
        "Unknown label status",
    )
    documents = manifest["documents"]
    require(8 <= len(documents) <= 12, "Expected 8–12 documents")
    require({d["format"] for d in documents} == {"pdf", "docx", "txt", "md"}, "Format coverage")
    for entry in documents + manifest["fixtures"]:
        actual = hashlib.sha256(safe_path(root, entry["path"]).read_bytes()).hexdigest()
        require(actual == entry["sha256"], "Artifact checksum mismatch")
    for name, key in [
        ("questions.jsonl", "questions_sha256"),
        ("source_blocks.json", "source_blocks_sha256"),
    ]:
        require(
            hashlib.sha256((root / name).read_bytes()).hexdigest() == manifest[key],
            "Label checksum mismatch",
        )
    blocks = json.loads((root / "source_blocks.json").read_text(encoding="utf-8"))
    questions = [
        json.loads(line)
        for line in (root / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    require(
        len(questions) == manifest["question_count"] and 30 <= len(questions) <= 60,
        "Question count",
    )
    validate_questions(questions, blocks, documents)
    require({q["question_type"] for q in questions} == QUESTION_TYPES, "Question type coverage")
    require(
        sum(q["expected_abstain"] for q in questions) >= 5, "Need at least 5 unanswerable questions"
    )
    require(
        all(
            any(q["expected_abstain"] and q["split"] == split for q in questions)
            for split in ["dev", "test"]
        ),
        "Unanswerable split coverage",
    )
    inspect_corpus(root, documents, blocks)
    inspect_fixtures(root)
    with (root / "human_review.csv").open(encoding="utf-8", newline="") as stream:
        reviews = list(csv.DictReader(stream))
    require(len(reviews) == len(questions), "Review row count mismatch")
    review_by_id = {row["question_id"]: row for row in reviews}
    require(len(review_by_id) == len(reviews), "Duplicate review row")
    for q in questions:
        row = review_by_id.get(q["id"])
        require(row is not None and row["split"] == q["split"], "Review/question mismatch")
        require(
            row["status"] in {"pending", "approved", "changes_requested"}, "Unknown review status"
        )
        if row["status"] == "approved":
            require(bool(row["annotator"].strip()), "Approved review needs human annotator")
            require(bool(row["reviewer"].strip()), "Approved review needs independent reviewer")
            require(
                row["annotator"].strip().casefold() != row["reviewer"].strip().casefold(),
                "Annotator and reviewer must be different people",
            )
    approved = sum(row["status"] == "approved" for row in reviews)
    if require_reviewed or manifest["label_status"] == "human_reviewed":
        require(approved == len(questions), "Independent human review is incomplete")
        require(
            manifest["label_status"] == "human_reviewed",
            "Publish a reviewed snapshot before final benchmark",
        )
    return {
        "structural_validation": "passed",
        "documents": len(documents),
        "fixtures": len(manifest["fixtures"]),
        "source_blocks": len(blocks),
        "questions": len(questions),
        "splits": dict(Counter(q["split"] for q in questions)),
        "question_types": dict(Counter(q["question_type"] for q in questions)),
        "unanswerable": sum(q["expected_abstain"] for q in questions),
        "human_approved": approved,
        "label_status": manifest["label_status"],
        "parser_span_mapping": manifest["parser_span_mapping"],
        "model_benchmark": "not_run",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path(__file__).parent / "datasets")
    parser.add_argument("--require-reviewed", action="store_true")
    args = parser.parse_args()
    try:
        result = validate(args.dataset, args.require_reviewed)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Dataset validation failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
