"""Real formats, source fidelity, resource bounds and exact embedding input budgets."""

import json
import zipfile
from pathlib import Path

import pytest
from docx import Document
from pydantic import ValidationError

from app.core.config import Settings
from app.services.chunking import ChunkConfig, E5TokenCounter, split_document
from app.services.parsing import (
    ParsedBlock,
    ParsedDocument,
    ParseError,
    ParseLimits,
    _parse_inline,
    normalize,
    parse_file,
    validate_docx_archive,
)

SNAPSHOT = Path(__file__).resolve().parents[2] / "eval/snapshots/reviewed-v1"
MANIFEST = json.loads((SNAPSHOT / "corpus_manifest.json").read_text(encoding="utf-8"))


class CharacterCounter:
    """Unit-only fake; one code point per token plus wrapper overhead."""

    def count(self, text):
        return len(text) + 4


@pytest.fixture(scope="module")
def e5_counter():
    from app.core.config import get_settings

    return E5TokenCounter(get_settings().hf_home / "hub")


@pytest.mark.parametrize("entry", MANIFEST["documents"], ids=lambda entry: entry["document_id"])
def test_real_corpus_chunk_round_trip(entry, e5_counter):
    parsed = parse_file(SNAPSHOT / entry["path"], entry["format"])
    chunks = split_document(parsed, e5_counter)
    assert chunks and all(chunk.text.strip() and chunk.token_count <= 350 for chunk in chunks)
    by_id = {block.block_id: block for block in parsed.blocks}
    coverage = {block.block_id: set() for block in parsed.blocks}
    for chunk in chunks:
        reconstructed = []
        pages = set()
        for span in chunk.source_spans:
            block = by_id[span["block_id"]]
            start, end = span["char_start"], span["char_end"]
            reconstructed.append(block.normalized_text[start:end])
            if span["role"] == "content":
                coverage[block.block_id].update(range(start, end))
            if "page_start" in block.location:
                pages.add(block.location["page_start"])
        assert "\n".join(reconstructed) == chunk.text
        assert e5_counter.count(chunk.text) == chunk.token_count
        assert len(pages) <= 1
    for block in parsed.blocks:
        assert coverage[block.block_id] == set(range(len(block.normalized_text)))
        assert normalize(block.raw_text) == block.normalized_text


@pytest.mark.parametrize(
    "name,code",
    [
        ("scan.pdf", "needs_ocr"),
        ("blank.pdf", "no_extractable_text"),
        ("encrypted.pdf", "encrypted_document"),
        ("malformed.pdf", "parse_failed"),
        ("spoofed.pdf", "unsupported_file_type"),
        ("malformed.docx", "parse_failed"),
    ],
)
def test_parser_fixture_errors(name, code):
    entry = next(item for item in MANIFEST["fixtures"] if Path(item["path"]).name == name)
    with pytest.raises(ParseError, match=code):
        parse_file(SNAPSHOT / entry["path"], Path(name).suffix[1:])


def test_mixed_pdf_keeps_actual_page_warning():
    entry = next(item for item in MANIFEST["fixtures"] if Path(item["path"]).name == "mixed.pdf")
    parsed = parse_file(SNAPSHOT / entry["path"], "pdf")
    assert parsed.warnings == [{"code": "partial_text_extraction", "skipped_pages": [2]}]
    assert {block.location["page_start"] for block in parsed.blocks} == {1}


def test_limits_and_hard_timeout(tmp_path):
    pdf = SNAPSHOT / next(
        d["path"] for d in MANIFEST["documents"] if d["document_id"] == "acceptance"
    )
    with pytest.raises(ParseError, match="document_limit_exceeded"):
        parse_file(pdf, "pdf", ParseLimits(max_pdf_pages=1))
    with pytest.raises(ParseError, match="parser_timeout"):
        parse_file(pdf, "pdf", ParseLimits(timeout_seconds=0.001))
    text = tmp_path / "input.txt"
    text.write_text("alpha\nbeta", encoding="utf-8")
    for limits in [ParseLimits(max_extracted_chars=4), ParseLimits(max_source_blocks=1)]:
        with pytest.raises(ParseError, match="document_limit_exceeded"):
            _parse_inline(text, "txt", limits)


def test_docx_table_header_and_order_have_provenance(tmp_path):
    path = tmp_path / "table.docx"
    doc = Document()
    doc.add_heading("Điều kiện", level=1)
    doc.add_paragraph("Trước bảng.")
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Mã", "Giới hạn"
    for number in range(12):
        row = table.add_row()
        row.cells[0].text = f"BM-{number:02d}"
        row.cells[1].text = "Được duyệt trong vòng 03 ngày làm việc."
    doc.add_paragraph("Sau bảng.")
    doc.save(path)
    parsed = parse_file(path, "docx")
    chunks = split_document(parsed, CharacterCounter(), ChunkConfig(110, 10))
    header = next(b for b in parsed.blocks if b.location.get("row_start") == 1)
    for chunk in chunks:
        if any(loc.get("row_start", 0) > 1 for loc in chunk.location["locations"]):
            assert any(
                s["block_id"] == header.block_id and s["role"] == "context"
                for s in chunk.source_spans
            )
    assert parsed.blocks[-1].normalized_text == "Sau bảng."
    assert parsed.blocks[-1].location == {"kind": "docx_block", "block_start": 3, "block_end": 3}
    assert all("page_start" not in block.location for block in parsed.blocks)


def test_archive_limits_checked_before_xml(tmp_path):
    path = tmp_path / "limited.docx"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "x")
        archive.writestr("word/document.xml", "a" * (1024**2 + 1))
    for limits in [ParseLimits(max_docx_zip_entries=1), ParseLimits(max_docx_uncompressed_mb=1)]:
        with pytest.raises(ParseError, match="document_limit_exceeded"):
            validate_docx_archive(path, limits)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../outside.xml", "do not extract")
    with pytest.raises(ParseError, match="parse_failed"):
        validate_docx_archive(path, ParseLimits())
    assert not (tmp_path.parent / "outside.xml").exists()


def test_utf8_bom_nfd_crlf_and_literal_html(tmp_path):
    path = tmp_path / "source.md"
    path.write_bytes(
        "\ufeff# Chính sách\r\n\r\nTo\u0302i giữ <script>alert(1)</script>.\r\n".encode()
    )
    parsed = parse_file(path, "md")
    assert parsed.blocks[1].normalized_text == "Tôi giữ <script>alert(1)</script>."
    assert parsed.blocks[1].location["line_start"] == 3
    assert "\r\n" in parsed.blocks[1].raw_text
    assert parsed.blocks[1].context_ids == [parsed.blocks[0].block_id]
    path.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(ParseError, match="unsupported_encoding"):
        parse_file(path, "md")


def test_long_vietnamese_block_no_truncation_or_gap(e5_counter):
    text = "Điều kiện áp dụng BM-09: gửi trước ba ngày làm việc. " * 90
    block = ParsedBlock(
        "b000001", text, normalize(text), {"kind": "line_range", "line_start": 1, "line_end": 1}
    )
    chunks = split_document(ParsedDocument([block]), e5_counter)
    assert len(chunks) > 2
    covered = set()
    for chunk in chunks:
        span = chunk.source_spans[0]
        covered.update(range(span["char_start"], span["char_end"]))
        assert chunk.token_count == e5_counter.count(chunk.text) <= 350
    assert covered == set(range(len(block.normalized_text)))
    assert chunks[1].source_spans[0]["char_start"] < chunks[0].source_spans[0]["char_end"]
    with pytest.raises(ParseError, match="document_limit_exceeded"):
        split_document(ParsedDocument([block]), e5_counter, ChunkConfig(max_chunks=1))


def test_settings_reject_incompatible_chunker():
    base = {"_env_file": None, "database_url": "postgresql+psycopg://user@localhost/dev"}
    with pytest.raises(ValidationError):
        Settings(**base, chunk_size_tokens=50, chunk_overlap_tokens=50)
    with pytest.raises(ValidationError):
        Settings(**base, embedding_revision="different-model")


def test_e5_counter_includes_actual_prefix_and_special_tokens(e5_counter):
    tokenizer = e5_counter.tokenizer
    text = "Điều kiện BM-09"
    assert e5_counter.count(text) == len(tokenizer.encode("passage: " + text).ids)
    assert e5_counter.count(text) > len(tokenizer.encode(text, add_special_tokens=False).ids)
    assert e5_counter.count_query(text) == len(tokenizer.encode("query: " + text).ids)


def test_adversarial_document_remains_inert_data():
    entry = next(item for item in MANIFEST["fixtures"] if "prompt_injection" in item["path"])
    parsed = parse_file(SNAPSHOT / entry["path"], "txt")
    assert parsed.blocks and not parsed.warnings
    assert all(normalize(block.raw_text) == block.normalized_text for block in parsed.blocks)
