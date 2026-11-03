"""Bind immutable reviewed author spans to production parser/chunker output; no inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.services.chunking import (  # noqa: E402
    CHUNKER_VERSION,
    E5_MODEL,
    E5_REVISION,
    ChunkConfig,
    E5TokenCounter,
    split_document,
)
from app.services.parsing import PARSER_VERSION, normalize, parse_file  # noqa: E402
from eval.validate_dataset import safe_path, validate  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def location_matches(actual: dict, gold: dict) -> bool:
    return all(actual.get(key) == value for key, value in gold.items())


def map_quote(blocks: list[dict], quote: str, location: dict) -> list[dict]:
    candidates = [block for block in blocks if location_matches(block["location"], location)]
    combined = " ".join(block["normalized_text"] for block in candidates)
    quote = normalize(quote)
    start = combined.find(quote)
    if start < 0 or combined.find(quote, start + 1) >= 0:
        raise ValueError("Gold quote missing or ambiguous at its declared source location")
    end = start + len(quote)
    spans, offset = [], 0
    for block in candidates:
        block_end = offset + len(block["normalized_text"])
        if start < block_end and end > offset:
            spans.append(
                {
                    "block_id": block["block_id"],
                    "char_start": max(0, start - offset),
                    "char_end": min(block_end, end) - offset,
                }
            )
        offset = block_end + 1
    return spans


def build_mapping(root: Path, counter, config: ChunkConfig | None = None) -> dict:
    validate(root, require_reviewed=True)
    config = config or ChunkConfig()
    manifest = json.loads((root / "corpus_manifest.json").read_text(encoding="utf-8"))
    author = json.loads((root / "source_blocks.json").read_text(encoding="utf-8"))
    questions = [
        json.loads(line)
        for line in (root / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    documents = {}
    for entry in manifest["documents"]:
        parsed = parse_file(safe_path(root, entry["path"]), entry["format"])
        chunks = split_document(parsed, counter, config)
        documents[entry["document_id"]] = {
            "sha256": entry["sha256"],
            "version": entry["version"],
            "blocks": [asdict(block) for block in parsed.blocks],
            "chunks": [asdict(chunk) for chunk in chunks],
            "warnings": parsed.warnings,
        }
    source_mapping = {}
    for block in author:
        parsed = documents[block["document_id"]]["blocks"]
        source_mapping[block["source_block_id"]] = {
            "document_id": block["document_id"],
            "spans": map_quote(parsed, block["text"], block["location"]),
        }
    mapped_questions = []
    for question in questions:
        evidence = []
        for gold in question["gold_evidence"]:
            document = documents[gold["document_id"]]
            spans = map_quote(document["blocks"], gold["quote"], gold["location"])
            # Verify complete gold coverage by the union of content spans, without counting
            # repeated context headings as retrieved evidence or dropping difficult questions.
            for span in spans:
                covered = set()
                for chunk in document["chunks"]:
                    for actual in chunk["source_spans"]:
                        if actual["block_id"] == span["block_id"] and actual["role"] == "content":
                            covered.update(
                                range(
                                    max(actual["char_start"], span["char_start"]),
                                    min(actual["char_end"], span["char_end"]),
                                )
                            )
                if len(covered) != span["char_end"] - span["char_start"]:
                    raise ValueError("Chunk coverage lost gold evidence characters")
            evidence.append(
                {
                    "evidence_id": gold["evidence_id"],
                    "evidence_group_id": gold["evidence_group_id"],
                    "document_id": gold["document_id"],
                    "quote": gold["quote"],
                    "author_span": {
                        key: gold[key] for key in ("source_block_id", "char_start", "char_end")
                    },
                    "parser_spans": spans,
                }
            )
        mapped_questions.append({"id": question["id"], "evidence": evidence})
    return {
        "mapping_version": "reviewed-v1-source-v1-e5-350-v1",
        "dataset_version": manifest["dataset_version"],
        "parent_manifest_sha256": digest(root / "corpus_manifest.json"),
        "questions_sha256": digest(root / "questions.jsonl"),
        "human_review_sha256": digest(root / "human_review.csv"),
        "parser_version": PARSER_VERSION,
        "chunker_version": CHUNKER_VERSION,
        "tokenizer": {
            "model": E5_MODEL,
            "revision": E5_REVISION,
            "prefix": "passage: ",
            "special_tokens": True,
        },
        "chunk_config": asdict(config),
        "documents": documents,
        "source_mapping": source_mapping,
        "questions": mapped_questions,
        "question_count": len(questions),
        "source_block_count": len(author),
        "evidence_count": sum(len(q["evidence"]) for q in mapped_questions),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "eval/snapshots/reviewed-v1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    settings = get_settings()
    report = build_mapping(args.dataset, E5TokenCounter(settings.hf_home / "hub"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # No overwriting a previous result, including a human-edited or committed artifact.
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {key: report[key] for key in ("question_count", "source_block_count", "evidence_count")}
        )
    )


if __name__ == "__main__":
    main()
