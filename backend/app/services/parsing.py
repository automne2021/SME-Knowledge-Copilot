"""Bounded, offline parsers. Locations and code-point spans refer to stored NFC text."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath

PARSER_VERSION = "source-v1-nfc-ws-shy-pymupdf1.28.2-docx1.2.0"


class ParseError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ParseLimits:
    max_pdf_pages: int = 200
    max_docx_uncompressed_mb: int = 100
    max_docx_zip_entries: int = 2000
    max_extracted_chars: int = 2_000_000
    max_source_blocks: int = 20_000
    timeout_seconds: float = 60


@dataclass
class ParsedBlock:
    block_id: str
    raw_text: str
    normalized_text: str
    location: dict
    context_ids: list[str] = field(default_factory=list)


@dataclass
class ParsedDocument:
    blocks: list[ParsedBlock]
    warnings: list[dict] = field(default_factory=list)
    parser_version: str = PARSER_VERSION


def normalize(text: str) -> str:
    # PDF extraction of BM-09 in the frozen corpus uses U+00AD for the printed hyphen.
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text.replace("\u00ad", "-"))).strip()


def validate_docx_archive(path: Path, limits: ParseLimits) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if (
                len(infos) > limits.max_docx_zip_entries
                or sum(item.file_size for item in infos) > limits.max_docx_uncompressed_mb * 1024**2
            ):
                raise ParseError("document_limit_exceeded")
            names = set()
            for info in infos:
                name = info.filename
                if (
                    info.flag_bits & 1
                    or name in names
                    or "\\" in name
                    or ":" in name
                    or PurePosixPath(name).is_absolute()
                    or ".." in PurePosixPath(name).parts
                ):
                    raise ParseError("parse_failed")
                names.add(name)
            if not {"[Content_Types].xml", "word/document.xml"} <= names:
                raise ParseError("parse_failed")
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        raise ParseError("parse_failed") from exc


def _parse_inline(path: Path, file_format: str, limits: ParseLimits) -> ParsedDocument:
    blocks: list[ParsedBlock] = []
    warnings: list[dict] = []
    total_chars = 0

    def add(raw: str, location: dict, context: list[str] | None = None) -> ParsedBlock | None:
        nonlocal total_chars
        text = normalize(raw)
        if not text:
            return None
        total_chars += len(raw) + len(text)
        if total_chars > limits.max_extracted_chars or len(blocks) >= limits.max_source_blocks:
            raise ParseError("document_limit_exceeded")
        block = ParsedBlock(f"b{len(blocks) + 1:06d}", raw, text, location, list(context or []))
        blocks.append(block)
        return block

    try:
        if file_format == "pdf":
            import pymupdf

            if not path.read_bytes()[:5] == b"%PDF-":
                raise ParseError("unsupported_file_type")
            with pymupdf.open(path) as document:
                if document.needs_pass:
                    raise ParseError("encrypted_document")
                if len(document) > limits.max_pdf_pages:
                    raise ParseError("document_limit_exceeded")
                skipped = []
                for number, page in enumerate(document, 1):
                    page_blocks = page.get_text("blocks", sort=True)
                    text_blocks = [
                        item for item in page_blocks if item[6] == 0 and normalize(item[4])
                    ]
                    if not text_blocks and page.get_images():
                        skipped.append(number)
                    # P0 supports simple ruled tables. Keep row/header provenance and
                    # remove their text from ordinary blocks to avoid duplicate evidence.
                    tables = page.find_tables(strategy="lines_strict").tables
                    items = []
                    for item in text_blocks:
                        if not any(
                            pymupdf.Rect(item[:4]).intersects(table.bbox) for table in tables
                        ):
                            items.append((list(item[:4]), item[4], None, None))
                    if tables:
                        for text_block in page.get_text("dict")["blocks"]:
                            for line in text_block.get("lines", []):
                                rectangle = pymupdf.Rect(line["bbox"])
                                if any(rectangle.intersects(table.bbox) for table in tables):
                                    continue
                                if any(
                                    rectangle.intersects(item[:4])
                                    for item in text_blocks
                                    if not any(
                                        pymupdf.Rect(item[:4]).intersects(table.bbox)
                                        for table in tables
                                    )
                                ):
                                    continue
                                raw = "".join(span["text"] for span in line["spans"])
                                items.append((list(line["bbox"]), raw, None, None))
                    for table_number, table in enumerate(tables, 1):
                        if table.header.external:
                            items.append(
                                (
                                    list(table.header.bbox),
                                    " | ".join(table.header.names),
                                    table_number,
                                    0,
                                )
                            )
                        for row_index, row in enumerate(table.extract()):
                            items.append(
                                (
                                    list(table.rows[row_index].bbox),
                                    " | ".join(cell or "" for cell in row),
                                    table_number,
                                    row_index + 1,
                                )
                            )
                    headers = {}
                    for index, (bbox, raw, table_number, row_number) in enumerate(
                        sorted(items, key=lambda item: (item[0][1], item[0][0])), 1
                    ):
                        location = {
                            "kind": "pdf_page",
                            "page_start": number,
                            "page_end": number,
                            "block_start": index,
                            "block_end": index,
                            "bbox": bbox,
                        }
                        if table_number is not None:
                            location.update(
                                table=table_number, row_start=row_number, row_end=row_number
                            )
                        block = add(
                            raw,
                            location,
                            [headers[table_number]] if table_number in headers else [],
                        )
                        if block and table_number is not None and table_number not in headers:
                            headers[table_number] = block.block_id
                if not blocks and skipped:
                    raise ParseError("needs_ocr")
                if skipped:
                    warnings.append({"code": "partial_text_extraction", "skipped_pages": skipped})
        elif file_format == "docx":
            from docx import Document
            from docx.table import Table

            validate_docx_archive(path, limits)
            document = Document(path)
            headings: list[str] = []
            paragraph_number = table_number = 0
            # Body order is retained. Header/footer text is explicitly outside this P0 contract.
            for item in document.iter_inner_content():
                if isinstance(item, Table):
                    table_number += 1
                    header_id = None
                    for row_number, row in enumerate(item.rows, 1):
                        raw = " | ".join(cell.text for cell in row.cells)
                        context = headings + ([header_id] if header_id else [])
                        block = add(
                            raw,
                            {
                                "kind": "docx_table",
                                "table": table_number,
                                "row_start": row_number,
                                "row_end": row_number,
                            },
                            context,
                        )
                        if row_number == 1 and block:
                            header_id = block.block_id
                else:
                    paragraph_number += 1
                    style = item.style.name if item.style else ""
                    match = re.fullmatch(r"Heading (\d+)", style)
                    block = add(
                        item.text,
                        {
                            "kind": "docx_block",
                            "block_start": paragraph_number,
                            "block_end": paragraph_number,
                        },
                        headings,
                    )
                    if match and block:
                        level = int(match[1])
                        headings = headings[: level - 1] + [block.block_id]
        elif file_format in {"txt", "md"}:
            try:
                text = path.read_bytes().decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise ParseError("unsupported_encoding") from exc
            if any(unicodedata.category(c) == "Cc" and c not in "\t\r\n" for c in text):
                raise ParseError("unsupported_file_type")
            headings = []
            table_header = None
            for number, line in enumerate(text.splitlines(keepends=True), 1):
                match = re.match(r"^(#{1,6})\s+", line) if file_format == "md" else None
                if file_format == "md" and re.fullmatch(r"\s*\|?\s*:?-+.*", line) and "|" in line:
                    # The separator is still retained as source; it is not a data row.
                    pass
                elif "|" not in line:
                    table_header = None
                context = headings + ([table_header] if table_header else [])
                block = add(
                    line, {"kind": "line_range", "line_start": number, "line_end": number}, context
                )
                if block and file_format == "md" and "|" in line and not table_header:
                    table_header = block.block_id
                if match and block:
                    headings = headings[: len(match[1]) - 1] + [block.block_id]
        else:
            raise ParseError("unsupported_file_type")
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError("parse_failed") from exc
    if not blocks:
        raise ParseError("no_extractable_text")
    return ParsedDocument(blocks, warnings)


def parse_file(path: Path, file_format: str, limits: ParseLimits | None = None) -> ParsedDocument:
    """Hard wall timeout includes native PDF/XML calls; no model or network access."""
    limits = limits or ParseLimits()
    with tempfile.TemporaryDirectory(prefix="sme-parse-") as temporary:
        config = Path(temporary) / "config.json"
        result = Path(temporary) / "result.json"
        config.write_text(json.dumps(asdict(limits)), encoding="utf-8")
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "app.services.parsing",
                    str(path.resolve()),
                    file_format,
                    str(config),
                    str(result),
                ],
                timeout=limits.timeout_seconds,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                cwd=Path(__file__).resolve().parents[2],
            )
        except subprocess.TimeoutExpired as exc:
            raise ParseError("parser_timeout") from exc
        if completed.returncode or not result.is_file():
            raise ParseError("parse_failed")
        payload = json.loads(result.read_text(encoding="utf-8"))
        if "error" in payload:
            raise ParseError(payload["error"])
        return ParsedDocument(
            [ParsedBlock(**block) for block in payload["blocks"]],
            payload["warnings"],
            payload["parser_version"],
        )


if __name__ == "__main__":
    try:
        output = asdict(
            _parse_inline(
                Path(sys.argv[1]),
                sys.argv[2],
                ParseLimits(**json.loads(Path(sys.argv[3]).read_text())),
            )
        )
    except ParseError as error:
        output = {"error": error.code}
    Path(sys.argv[4]).write_text(json.dumps(output, ensure_ascii=False), encoding="utf-8")
