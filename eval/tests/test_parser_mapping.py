"""Mapping fails closed on quote/location drift; no model calls or relabeling."""

import json
from pathlib import Path

import pytest

from eval.parser_mapping import build_mapping, map_quote


def test_quote_crosses_parser_blocks_at_same_page():
    blocks = [
        {
            "block_id": "b1",
            "normalized_text": "Điều kiện gửi",
            "location": {"kind": "pdf_page", "page_start": 2, "page_end": 2},
        },
        {
            "block_id": "b2",
            "normalized_text": "trước 03 ngày.",
            "location": {"kind": "pdf_page", "page_start": 2, "page_end": 2},
        },
    ]
    spans = map_quote(blocks, "gửi trước 03", {"kind": "pdf_page", "page_start": 2, "page_end": 2})
    assert spans == [
        {"block_id": "b1", "char_start": 10, "char_end": 13},
        {"block_id": "b2", "char_start": 0, "char_end": 8},
    ]
    with pytest.raises(ValueError, match="missing or ambiguous"):
        map_quote(blocks, "gửi trước 03", {"kind": "pdf_page", "page_start": 1, "page_end": 1})


@pytest.mark.parametrize("text,quote", [("same same", "same"), ("changed policy", "old policy")])
def test_missing_or_ambiguous_quote_is_not_fuzzy_matched(text, quote):
    with pytest.raises(ValueError, match="missing or ambiguous"):
        map_quote([{"block_id": "b1", "normalized_text": text, "location": {}}], quote, {})


def test_frozen_mapping_reproduces_all_reviewed_questions():
    from app.core.config import get_settings
    from app.services.chunking import E5TokenCounter

    root = Path(__file__).resolve().parents[2]
    frozen = json.loads(
        (root / "eval/mappings/reviewed-v1-source-v1-e5-350-v1.json").read_text(encoding="utf-8")
    )
    actual = build_mapping(
        root / "eval/snapshots/reviewed-v1", E5TokenCounter(get_settings().hf_home / "hub")
    )
    assert actual == frozen
    assert actual["question_count"] == 45 and actual["source_block_count"] == 35
    assert actual["evidence_count"] == 47
