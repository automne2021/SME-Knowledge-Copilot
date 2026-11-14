"""Reproducible synthetic v2 documents; offline and separate from the v1 builder."""

from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from datetime import date
from html import escape
from importlib.metadata import version
from pathlib import Path

from eval.build_dataset import FIXED_TIME, json_bytes, put, sha256

ROOT = Path(__file__).resolve().parent
SEED = ROOT / "seeds/corpus_v2.json"
BLOCK_TYPES = {"heading", "paragraph", "list_item", "table", "page_break", "signature"}
DEFAULT_FONT = Path("C:/Windows/Fonts/times.ttf")


def validate_seed(seed: dict) -> None:
    """Validate a staged corpus without pretending unwritten documents are complete."""
    if not isinstance(seed, dict):
        raise ValueError("Seed must be an object")
    if seed.get("corpus_version") != "synthetic-sme-v2":
        raise ValueError("Unsupported corpus_version")
    for field in ("company", "notice"):
        if not isinstance(seed.get(field), str) or not seed[field].strip():
            raise ValueError(f"Missing {field}")
    documents = seed.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("documents must be a nonempty list")
    ids, names = set(), set()
    for doc in documents:
        if not isinstance(doc, dict):
            raise ValueError("Document must be an object")
        doc_id, name = doc.get("document_id", ""), doc.get("file_name", "")
        if not isinstance(doc_id, str) or not re.fullmatch(r"D(?:0[1-9]|1[0-4])", doc_id):
            raise ValueError("Invalid document_id")
        if doc_id in ids or (isinstance(name, str) and name in names):
            raise ValueError("Duplicate document_id or file_name")
        ids.add(doc_id)
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[a-z0-9_]+\.(?:docx|pdf|md|txt)", name)
            or not isinstance(doc.get("format"), str)
            or doc.get("format") not in {"docx", "pdf", "md", "txt", "scan"}
            or Path(name).suffix != "." + ("pdf" if doc["format"] == "scan" else doc["format"])
        ):
            raise ValueError("Invalid file_name/format")
        names.add(name)
        for field in ("title", "doc_number", "effective_date", "issue_line"):
            if not isinstance(doc.get(field), str) or not doc[field].strip():
                raise ValueError(f"Missing {field}")
        date.fromisoformat(doc["effective_date"])
        if not isinstance(doc.get("blocks"), list) or not doc["blocks"]:
            raise ValueError("Missing blocks")
        for block in doc["blocks"]:
            if not isinstance(block, dict):
                raise ValueError("Block must be an object")
            kind = block.get("type")
            if not isinstance(kind, str) or kind not in BLOCK_TYPES:
                raise ValueError("Unknown block type")
            facts = block.get("facts", [])
            if not isinstance(facts, list) or any(
                not isinstance(fact, str) or not re.fullmatch(r"F-[A-Z]+-\d{2}", fact)
                for fact in facts
            ):
                raise ValueError("Invalid facts")
            if kind in {"heading", "paragraph", "list_item"}:
                if not isinstance(block.get("text"), str) or not block["text"].strip():
                    raise ValueError("Empty block text")
            if kind == "heading" and (
                type(block.get("level")) is not int or not 1 <= block["level"] <= 6
            ):
                raise ValueError("Invalid heading level")
            if kind == "list_item" and type(block.get("ordered")) is not bool:
                raise ValueError("Missing ordered flag")
            if kind == "signature" and (
                not isinstance(block.get("lines"), list)
                or not block["lines"]
                or any(not isinstance(x, str) or not x.strip() for x in block["lines"])
            ):
                raise ValueError("Invalid signature")
            if kind == "table":
                header, rows = block.get("header"), block.get("rows")
                if (
                    not isinstance(header, list)
                    or not header
                    or not isinstance(rows, list)
                    or not rows
                ):
                    raise ValueError("Empty table")
                if any(not isinstance(x, str) or not x.strip() for x in header):
                    raise ValueError("Empty table header")
                if any(
                    not isinstance(row, list)
                    or len(row) != len(header)
                    or any(not isinstance(x, str) or not x.strip() for x in row)
                    for row in rows
                ):
                    raise ValueError("Invalid table row")
                widths = block.get("widths_cm", [17 / len(header)] * len(header))
                if (
                    not isinstance(widths, list)
                    or len(widths) != len(header)
                    or any(type(w) not in {int, float} or not 0 < w <= 17 for w in widths)
                    or abs(sum(widths) - 17) > 0.01
                ):
                    raise ValueError("Invalid table widths")


def docx_bytes(document: dict, company: str, notice: str) -> bytes:
    from docx import Document
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor

    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin, section.bottom_margin = Cm(2), Cm(2)
    section.left_margin, section.right_margin = Cm(2.2), Cm(1.8)
    section.header_distance, section.footer_distance = Cm(0.8), Cm(0.8)
    # The installed Word template may carry theme fonts and a blue title rule.
    for border in list(doc.styles.element.iter(qn("w:pBdr"))):
        border.getparent().remove(border)
    for name in ("Normal", "Title", "Heading 1", "Heading 2", "Heading 3", "Heading 4"):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        fonts = style.element.get_or_add_rPr().rFonts
        for attr in list(fonts.attrib):
            if "theme" in attr.lower():
                del fonts.attrib[attr]
        for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
            fonts.set(qn(f"w:{attr}"), "Times New Roman")
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.size = Pt(12.5 if name == "Normal" else 14)
        style.paragraph_format.space_after = Pt(5)
        style.paragraph_format.line_spacing = 1.05
    doc.styles["Normal"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    doc.styles["Title"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.styles["Title"].font.bold = True
    # Notice appears exactly once in the package, in the first-page header only.
    section.different_first_page_header_footer = True
    header = section.first_page_header.paragraphs[0]
    header.text = notice
    header.runs[0].font.size = Pt(8)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for text in (
        company.upper(),
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        "Độc lập – Tự do – Hạnh phúc",
        f"Số: {document['doc_number']}",
        document["issue_line"],
    ):
        p = doc.add_paragraph(text)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(3)
    doc.add_paragraph(document["title"], style="Title")
    p = doc.add_paragraph(f"Ngày hiệu lực: {document['effective_date']}")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for block in document["blocks"]:
        kind = block["type"]
        if kind == "heading":
            doc.add_heading(block["text"], level=block["level"])
        elif kind in {"paragraph", "list_item"}:
            style = None
            if kind == "list_item":
                style = "List Number" if block["ordered"] else "List Bullet"
            doc.add_paragraph(block["text"], style=style)
        elif kind == "page_break":
            doc.add_page_break()
        elif kind == "signature":
            for line in block["lines"]:
                p = doc.add_paragraph(line)
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif kind == "table":
            table = doc.add_table(rows=1, cols=len(block["header"]))
            table.style = "Table Grid"
            table.autofit = False
            widths = block.get("widths_cm", [17 / len(block["header"])] * len(block["header"]))
            for column, width in zip(table.columns, widths, strict=True):
                column.width = Cm(width)
            for row_data in [block["header"], *block["rows"]]:
                row = table.rows[0] if row_data is block["header"] else table.add_row()
                for cell, text, width in zip(row.cells, row_data, widths, strict=True):
                    cell.width = Cm(width)
                    cell.text = text
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    for p in cell.paragraphs:
                        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        p.paragraph_format.space_before = Pt(4)
                        p.paragraph_format.space_after = Pt(4)
                        for run in p.runs:
                            run.font.size = Pt(11)
                if row_data is block["header"]:
                    repeat = OxmlElement("w:tblHeader")
                    row._tr.get_or_add_trPr().append(repeat)
                    for cell in row.cells:
                        shade = OxmlElement("w:shd")
                        shade.set(qn("w:fill"), "EDEDED")
                        cell._tc.get_or_add_tcPr().append(shade)
                        for run in cell.paragraphs[0].runs:
                            run.bold = True
            doc.add_paragraph().paragraph_format.space_after = Pt(0)
    doc.core_properties.author = company
    doc.core_properties.title = document["title"]
    doc.core_properties.created = doc.core_properties.modified = FIXED_TIME
    raw, result = io.BytesIO(), io.BytesIO()
    doc.save(raw)
    with zipfile.ZipFile(raw) as source, zipfile.ZipFile(result, "w") as target:
        for name in sorted(source.namelist()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 2, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(info, source.read(name))
    return result.getvalue()


def pdf_bytes(document: dict, company: str, notice: str, font: Path) -> bytes:
    """Story paginates text; CSS draws real ruled tables, verified with lines_strict."""
    import pymupdf

    if not font.is_file():
        raise ValueError("PDF requires an existing Vietnamese font passed with --font")
    css = f"""
    @font-face {{font-family: Corpus; src: url('{font.name}');}}
    body {{font-family: Corpus; font-size: 12pt; line-height: 1.1;}}
    p {{margin: 0 0 7pt; text-align: justify;}}
    h1 {{font-size: 15pt; text-align: center; margin: 10pt 0;}}
    h2,h3,h4,h5,h6 {{font-size: 13pt; margin: 9pt 0 6pt;}}
    .admin {{text-align: center; margin: 0 0 3pt;}}
    .signature {{text-align: right;}}
    table {{border-collapse: collapse; width: 100%; margin: 8pt 0 10pt;}}
    th,td {{border: 0.6pt solid black; padding: 6pt; font-size: 11pt;}}
    th {{background-color: #eeeeee;}}
    """
    if document["format"] == "scan":
        # Blue entries simulate a filled paper form before rasterization.
        css += "td {font-style: italic; color: #173c73;}"
    parts = [
        "".join(
            f'<p class="admin">{escape(text)}</p>'
            for text in (
                company.upper(),
                "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
                "Độc lập – Tự do – Hạnh phúc",
                f"Số: {document['doc_number']}",
                document["issue_line"],
            )
        )
        + f"<h1>{escape(document['title'])}</h1>"
        + f'<p class="admin">Ngày hiệu lực: {escape(document["effective_date"])}</p>'
    ]
    for block in document["blocks"]:
        kind = block["type"]
        if kind == "page_break":
            parts.append("")
        elif kind == "heading":
            level = min(block["level"] + 1, 6)
            parts[-1] += f"<h{level}>{escape(block['text'])}</h{level}>"
        elif kind == "table":
            parts[-1] += (
                "<table><tr>"
                + "".join(f"<th>{escape(cell)}</th>" for cell in block["header"])
                + "</tr>"
            )
            for row in block["rows"]:
                parts[-1] += "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
            parts[-1] += "</table>"
        elif kind == "signature":
            parts[-1] += "".join(
                f'<p class="signature">{escape(line)}</p>' for line in block["lines"]
            )
        elif kind == "list_item":
            tag = "ol" if block["ordered"] else "ul"
            parts[-1] += f"<{tag}><li>{escape(block['text'])}</li></{tag}>"
        else:
            parts[-1] += f"<p>{escape(block['text'])}</p>"
    raw = io.BytesIO()
    writer = pymupdf.DocumentWriter(raw)
    page_box = pymupdf.Rect(0, 0, 595.28, 841.89)
    body_box = pymupdf.Rect(56, 62, 539, 786)

    def rectangle(number, filled):
        if number >= 200:
            raise ValueError("PDF pagination exceeded 200 pages")
        return page_box, body_box, None

    try:
        for part in parts:
            story = pymupdf.Story(part, user_css=css, archive=pymupdf.Archive(str(font.parent)))
            story.write(writer, rectangle)
    finally:
        writer.close()
    with pymupdf.open(stream=raw.getvalue(), filetype="pdf") as pdf:
        spare = pdf[0].insert_textbox(
            pymupdf.Rect(30, 24, 565, 45),
            notice,
            fontname="CorpusNotice",
            fontfile=str(font),
            fontsize=7,
            align=1,
        )
        if spare < 0:
            raise ValueError("PDF notice overflow")
        pdf.set_metadata(
            {"title": document["title"], "author": company, "producer": "synthetic-sme-v2"}
        )
        return pdf.tobytes(garbage=4, deflate=True, no_new_id=True)


def markdown_bytes(document: dict, company: str, notice: str) -> bytes:
    """Keep headings and table rows on stable UTF-8 source lines for gold spans."""
    parts = [
        notice,
        f"# {document['title']}",
        company,
        f"Số: {document['doc_number']}",
        document["issue_line"],
        f"Ngày hiệu lực: {document['effective_date']}",
    ]
    ordered_index = 0
    for block in document["blocks"]:
        kind = block["type"]
        if kind != "list_item" or not block.get("ordered"):
            ordered_index = 0
        if kind == "heading":
            parts.append("#" * min(block["level"] + 1, 6) + " " + block["text"])
        elif kind == "table":

            def row(cells):
                return (
                    "| "
                    + " | ".join(
                        cell.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")
                        for cell in cells
                    )
                    + " |"
                )

            parts.append(
                "\n".join(
                    [row(block["header"]), row(["---"] * len(block["header"]))]
                    + [row(cells) for cells in block["rows"]]
                )
            )
        elif kind == "signature":
            parts.append("\n\n".join(block["lines"]))
        elif kind == "list_item":
            ordered_index += int(block["ordered"])
            prefix = f"{ordered_index}." if block["ordered"] else "-"
            parts.append(f"{prefix} {block['text']}")
        elif kind != "page_break":
            parts.append(block["text"])
    return ("\n\n".join(parts) + "\n").encode("utf-8")


def text_bytes(document: dict, company: str, notice: str) -> bytes:
    """Plain email source: preserve the seed's From/To/Subject/Date lines verbatim."""
    parts = [notice]
    for block in document["blocks"]:
        kind = block["type"]
        if kind == "table":
            parts.append("\n".join(" | ".join(row) for row in [block["header"], *block["rows"]]))
        elif kind == "signature":
            parts.append("\n".join(block["lines"]))
        elif kind != "page_break":
            parts.append(("- " if kind == "list_item" else "") + block["text"])
    return ("\n\n".join(parts) + "\n").encode("utf-8")


def scan_bytes(document: dict, company: str, notice: str, font: Path) -> bytes:
    """Rasterize the complete seeded page at 150 dpi; publish no text or OCR layer."""
    import pymupdf

    source = pdf_bytes(document, company, notice, font)
    with pymupdf.open(stream=source, filetype="pdf") as original, pymupdf.open() as scanned:
        for page in original:
            pixmap = page.get_pixmap(dpi=150, alpha=False)
            target = scanned.new_page(width=page.rect.width, height=page.rect.height)
            target.insert_image(target.rect, stream=pixmap.tobytes("png"))
        scanned.set_metadata(
            {"title": document["title"], "author": company, "producer": "synthetic-sme-v2"}
        )
        return scanned.tobytes(garbage=4, deflate=True, no_new_id=True)


def build(
    seed_path: Path = SEED, output: Path = ROOT / "datasets", font: Path = DEFAULT_FONT
) -> dict:
    seed_data = seed_path.read_bytes()
    seed = json.loads(seed_data)
    validate_seed(seed)
    artifacts = {}
    documents = []
    for doc in seed["documents"]:
        if doc["format"] == "docx":
            data = docx_bytes(doc, seed["company"], seed["notice"])
        elif doc["format"] == "pdf":
            data = pdf_bytes(doc, seed["company"], seed["notice"], font)
        elif doc["format"] == "md":
            data = markdown_bytes(doc, seed["company"], seed["notice"])
        elif doc["format"] == "txt":
            data = text_bytes(doc, seed["company"], seed["notice"])
        elif doc["format"] == "scan":
            data = scan_bytes(doc, seed["company"], seed["notice"], font)
        else:
            raise ValueError("Unsupported document format")
        path = f"corpus_v2/{doc['file_name']}"
        artifacts[path] = data
        documents.append(
            {
                "document_id": doc["document_id"],
                "path": path,
                "format": doc["format"],
                "sha256": sha256(data),
                "facts": sorted({f for b in doc["blocks"] for f in b.get("facts", [])}),
            }
        )
    manifest = {
        "corpus_version": seed["corpus_version"],
        "corpus_seed_sha256": sha256(seed_data),
        "libraries": {"python-docx": version("python-docx"), "PyMuPDF": version("PyMuPDF")},
        "pdf_font_sha256": sha256(font.read_bytes())
        if any(d["format"] in {"pdf", "scan"} for d in seed["documents"])
        else None,
        "documents": documents,
    }
    artifacts["corpus_v2_manifest.json"] = json_bytes(manifest)
    # Preflight every artifact before any write, including an existing manifest.
    for name, data in artifacts.items():
        path = output / name
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"Artifact differs; use a new output directory/version: {path.name}")
    for name, data in artifacts.items():
        put(output / name, data)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, default=SEED)
    parser.add_argument("--output", type=Path, default=ROOT / "datasets")
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT)
    args = parser.parse_args()
    print(json.dumps(build(args.seed, args.output, args.font), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
