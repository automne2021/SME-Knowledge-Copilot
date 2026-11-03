"""Small ruled PDF table: page/row/header provenance survives serialization and splitting."""

import pymupdf

from app.services.chunking import ChunkConfig, split_document
from app.services.parsing import parse_file
from tests.test_parsing_chunking import CharacterCounter


def test_pdf_ruled_table_header_and_surrounding_text(tmp_path):
    path = tmp_path / "ruled.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((50, 35), "Before table")
        for x in (50, 160, 340):
            page.draw_line((x, 50), (x, 170))
        for y in (50, 80, 110, 140, 170):
            page.draw_line((50, y), (340, y))
        for row, values in enumerate(
            [
                ("Code", "Window"),
                ("BM-01", "Three days"),
                ("BM-02", "Four days"),
                ("BM-03", "Five days"),
            ]
        ):
            for x, value in zip((60, 170), values, strict=True):
                page.insert_text((x, 70 + row * 30), value)
        page.insert_text((50, 200), "After table")
        doc.save(path)
    parsed = parse_file(path, "pdf")
    assert parsed.blocks[0].normalized_text == "Before table"
    assert parsed.blocks[-1].normalized_text == "After table"
    header = next(block for block in parsed.blocks if block.location.get("row_start") == 1)
    assert header.normalized_text == "Code | Window"
    chunks = split_document(parsed, CharacterCounter(), ChunkConfig(40, 4))
    for chunk in chunks:
        if any(loc.get("row_start", 0) > 1 for loc in chunk.location["locations"]):
            assert any(
                span["role"] == "context" and span["block_id"] == header.block_id
                for span in chunk.source_spans
            )
        assert {loc["page_start"] for loc in chunk.location["locations"]} == {1}
