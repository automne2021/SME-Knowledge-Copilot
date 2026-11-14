"""Staged corpus checks use real DOCX/parser/tokenizer, never a provider or DB."""

import copy
import io
import json
import re
import zipfile

import pytest
from docx import Document

from eval.build_corpus_v2 import DEFAULT_FONT, SEED, build, docx_bytes, pdf_bytes, validate_seed


@pytest.fixture
def seed():
    return json.loads(SEED.read_text(encoding="utf-8"))


def test_stage_fact_coverage_and_unanswerable_exclusions(seed):
    validate_seed(seed)
    assert {d["document_id"] for d in seed["documents"]} == {"D02", "D03", "D04", "D05"}
    registry = (SEED.parents[2] / "docs/roadmap/01-corpus-v2-spec.md").read_text(encoding="utf-8")
    known = set(re.findall(r"^\| (F-[A-Z]+-\d{2}) \|", registry, re.M))
    for doc in seed["documents"]:
        expected = set(
            re.findall(rf"^\| (F-[A-Z]+-\d{{2}}) \|.*?\| {doc['document_id']} \|", registry, re.M)
        )
        actual = {f for b in doc["blocks"] for f in b.get("facts", [])}
        assert expected <= actual <= known
        if doc["document_id"] == "D02":
            assert "F-HR-04" in actual  # Registry notes its new deadline in D02.
        body = json.dumps(doc["blocks"], ensure_ascii=False).lower()
        for forbidden in (
            "phụ cấp gửi xe",
            "thưởng tết",
            "công tác nước ngoài",
            "trong bộ dữ liệu mẫu",
        ):
            assert forbidden not in body


@pytest.mark.parametrize(
    "field,value",
    [("corpus_version", "v1"), ("company", ""), ("notice", None), ("documents", [])],
)
def test_invalid_seed_metadata(seed, field, value):
    seed[field] = value
    with pytest.raises(ValueError):
        validate_seed(seed)


@pytest.mark.parametrize(
    "field,value",
    [
        ("document_id", "D15"),
        ("file_name", "../escape.docx"),
        ("file_name", "C:\\escape.docx"),
        ("file_name", "test.pdf"),
        ("format", "exe"),
        ("title", " "),
        ("issue_line", None),
        ("effective_date", "2026-02-30"),
        ("blocks", []),
    ],
)
def test_invalid_document_metadata(seed, field, value):
    seed["documents"][0][field] = value
    with pytest.raises(ValueError):
        validate_seed(seed)


@pytest.mark.parametrize(
    "block",
    [
        {"type": "unknown"},
        {"type": "paragraph", "text": ""},
        {"type": "paragraph", "text": "test", "facts": "F-CT-01"},
        {"type": "paragraph", "text": "test", "facts": ["unknown"]},
        {"type": "heading", "text": "test", "level": True},
        {"type": "heading", "text": "test", "level": 7},
        {"type": "list_item", "text": "test"},
        {"type": "signature", "lines": []},
        {"type": "table", "header": [], "rows": []},
        {"type": "table", "header": ["A"], "rows": [["x", "y"]]},
        {"type": "table", "header": ["A"], "rows": [[""]]},
        {"type": "table", "header": ["A"], "rows": [["x"]], "widths_cm": [18]},
    ],
)
def test_invalid_blocks(seed, block):
    seed["documents"][0]["blocks"] = [block]
    with pytest.raises(ValueError):
        validate_seed(seed)


def test_duplicate_document_or_file(seed):
    seed["documents"].append(copy.deepcopy(seed["documents"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        validate_seed(seed)
    seed["documents"][1]["document_id"] = "D02"
    with pytest.raises(ValueError, match="Duplicate"):
        validate_seed(seed)


def test_deterministic_bytes_and_refuse_modified_output(tmp_path):
    first = build(output=tmp_path / "a")
    assert build(output=tmp_path / "a") == first
    assert build(output=tmp_path / "b") == first
    for p in (tmp_path / "a").rglob("*"):
        if p.is_file():
            assert p.read_bytes() == (tmp_path / "b" / p.relative_to(tmp_path / "a")).read_bytes()
    changed = tmp_path / "a" / first["documents"][0]["path"]
    changed.write_bytes(b"human edit")
    with pytest.raises(ValueError, match="Artifact differs"):
        build(output=tmp_path / "a")
    assert changed.read_bytes() == b"human edit"


def test_checked_in_manifest_and_artifacts_match_rebuild(tmp_path):
    from eval.build_dataset import sha256

    dataset = SEED.parent.parent / "datasets"
    saved = json.loads((dataset / "corpus_v2_manifest.json").read_text(encoding="utf-8"))
    assert build(output=tmp_path) == saved
    for item in saved["documents"]:
        data = (dataset / item["path"]).read_bytes()
        assert sha256(data) == item["sha256"]
        assert data == (tmp_path / item["path"]).read_bytes()


def test_manifest_conflict_preflight_does_not_write_documents(tmp_path):
    manifest = tmp_path / "corpus_v2_manifest.json"
    manifest.write_text("edited", encoding="utf-8")
    with pytest.raises(ValueError, match="Artifact differs"):
        build(output=tmp_path)
    assert not (tmp_path / "corpus_v2").exists()
    assert manifest.read_text(encoding="utf-8") == "edited"


def test_docx_structure_notice_tables_and_fixed_zip(seed):
    data = docx_bytes(seed["documents"][0], seed["company"], seed["notice"])
    doc = Document(io.BytesIO(data))
    assert len(doc.tables) == 2
    assert any(p.style.name == "Title" for p in doc.paragraphs)
    assert any(p.style.name == "Heading 1" for p in doc.paragraphs)
    assert any(p.style.name == "Heading 2" for p in doc.paragraphs)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert all(i.date_time == (2026, 11, 2, 0, 0, 0) for i in archive.infolist())
        xml = "".join(archive.read(n).decode() for n in archive.namelist() if n.endswith(".xml"))
        assert xml.count(seed["notice"]) == 1
    table = doc.tables[0]
    assert [[c.text for c in row.cells] for row in table.rows][1:] == [
        ["Nhân viên", "300.000", "220.000", "900.000", "650.000"],
        ["Trưởng nhóm", "350.000", "260.000", "1.100.000", "800.000"],
        ["Trưởng phòng trở lên", "450.000", "320.000", "1.500.000", "1.000.000"],
    ]
    assert all(t.style.name == "Table Grid" for t in doc.tables)
    assert not list(
        doc.styles.element.iter(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pBdr"
        )
    )


def test_approved_d03_is_byte_identical(seed):
    from eval.build_dataset import sha256

    doc = next(d for d in seed["documents"] if d["document_id"] == "D03")
    assert sha256(docx_bytes(doc, seed["company"], seed["notice"])) == (
        "575b0c21c6bc6d164820a8b053a6e9612e4191f97bd9c915b30b182ba5f0a21c"
    )


@pytest.mark.parametrize("doc_id", ["D02", "D03", "D05"])
def test_every_docx_has_one_notice_and_no_duplicate_paragraphs(seed, doc_id):
    source = next(d for d in seed["documents"] if d["document_id"] == doc_id)
    data = docx_bytes(source, seed["company"], seed["notice"])
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        xml = "".join(archive.read(n).decode() for n in archive.namelist() if n.endswith(".xml"))
        assert xml.count(seed["notice"]) == 1
    paragraphs = [b["text"] for b in source["blocks"] if b["type"] == "paragraph"]
    assert len(paragraphs) == len(set(paragraphs))


@pytest.mark.parametrize("ordered,style", [(True, "List Number"), (False, "List Bullet")])
def test_list_blocks_keep_ordered_semantics(seed, ordered, style):
    doc = copy.deepcopy(seed["documents"][0])
    doc["blocks"] = [{"type": "list_item", "ordered": ordered, "text": "Bước kiểm tra"}]
    validate_seed({**seed, "documents": [doc]})
    rendered = Document(io.BytesIO(docx_bytes(doc, seed["company"], seed["notice"])))
    assert rendered.paragraphs[-1].style.name == style


@pytest.mark.parametrize(
    "doc_id,min_chars,max_chars",
    [
        ("D02", 2500, 6000),
        ("D03", 10000, 15000),
        ("D04", 5000, 6000),
        ("D05", 7500, 12000),
    ],
)
def test_production_parser_length_and_real_chunks(tmp_path, doc_id, min_chars, max_chars):
    from app.core.config import get_settings
    from app.services.chunking import E5TokenCounter, split_document
    from app.services.parsing import parse_file

    manifest = build(output=tmp_path)
    item = next(d for d in manifest["documents"] if d["document_id"] == doc_id)
    parsed = parse_file(tmp_path / item["path"], item["format"])
    assert not parsed.warnings
    assert min_chars <= sum(len(b.normalized_text) for b in parsed.blocks) <= max_chars
    by_id = {b.block_id: b for b in parsed.blocks}
    rows = [b for b in parsed.blocks if "table" in b.location]
    if doc_id == "D03":
        assert len(rows) == 8
        assert {b.location["kind"] for b in rows} == {"docx_table"}
    elif doc_id == "D04":
        assert len(rows) == 5
        assert {b.location["kind"] for b in rows} == {"pdf_page"}
    else:
        assert not rows
    for table in {b.location["table"] for b in rows}:
        table_rows = [b for b in rows if b.location["table"] == table]
        header = table_rows[0]
        assert header.location["row_start"] == 1
        assert all(header.block_id in row.context_ids for row in table_rows[1:])
    counter = E5TokenCounter(get_settings().hf_home / "hub")
    chunks = split_document(parsed, counter)
    assert chunks and all(0 < c.token_count <= 350 for c in chunks)
    for chunk in chunks:
        for span in chunk.source_spans:
            assert (
                0
                <= span["char_start"]
                < span["char_end"]
                <= len(by_id[span["block_id"]].normalized_text)
            )


def test_pdf_pages_table_thresholds_notice_and_unicode(tmp_path, seed):
    import pymupdf

    manifest = build(output=tmp_path)
    item = next(d for d in manifest["documents"] if d["document_id"] == "D04")
    with pymupdf.open(tmp_path / item["path"]) as pdf:
        assert len(pdf) == 2
        text = " ".join(" ".join(p.get_text().split()) for p in pdf)
        assert text.count(seed["notice"]) == 1
        assert "Hội đồng quản trị" in text and "Kế toán trưởng" in text
        assert "\ufffd" not in text
        tables = pdf[0].find_tables(strategy="lines_strict").tables
        assert len(tables) == 1
        assert len(tables[0].extract()) == 5
        rows = [[" ".join(c.split()) for c in r] for r in tables[0].extract()]
        assert [r[0] for r in rows[1:]] == [
            "Dưới 10 triệu đồng",
            "Từ 10 đến 50 triệu đồng",
            "Trên 50 đến 200 triệu đồng",
            "Trên 200 triệu đồng",
        ]
        assert [r[1] for r in rows[1:]] == [
            "Trưởng phòng",
            "Trưởng phòng và Kế toán trưởng",
            "Tổng Giám đốc",
            "Hội đồng quản trị",
        ]


def test_missing_pdf_font_writes_nothing(tmp_path):
    with pytest.raises(ValueError, match="font"):
        build(output=tmp_path / "out", font=tmp_path / "missing.ttf")
    assert not (tmp_path / "out").exists()


def test_pdf_automatically_paginates_and_preserves_final_text(seed):
    import pymupdf

    doc = copy.deepcopy(next(d for d in seed["documents"] if d["document_id"] == "D04"))
    doc["blocks"] = [
        {"type": "paragraph", "text": f"Mục {i}: " + "Nội dung kiểm thử xuống trang. " * 10}
        for i in range(40)
    ] + [{"type": "paragraph", "text": "KẾT THÚC KIỂM THỬ PHÂN TRANG"}]
    data = pdf_bytes(doc, seed["company"], seed["notice"], DEFAULT_FONT)
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        assert len(pdf) > 2
        text = " ".join(" ".join(p.get_text().split()) for p in pdf)
        assert "KẾT THÚC KIỂM THỬ PHÂN TRANG" in text
        for i in range(40):
            assert f"Mục {i}:" in text


def test_conflict_and_quote_policy_are_explicit(seed):
    docs = {d["document_id"]: d for d in seed["documents"]}
    hr = " ".join(b.get("text", "") for b in docs["D02"]["blocks"])
    assert "14 ngày" in hr and "thay thế mức 12 ngày" in hr and "01/01/2026" in hr
    assert "tối đa 5 ngày" in hr and "31/03" in hr and "30/06" in hr
    purchasing = " ".join(b.get("text", "") for b in docs["D05"]["blocks"])
    assert "từ 20 triệu đồng" in purchasing and "ít nhất 3 báo giá" in purchasing
    assert "09/2026/QĐ-TL" in purchasing
