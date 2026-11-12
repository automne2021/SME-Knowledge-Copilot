"""Offline, literal-text review packets and independent reviewer files; no auto scores."""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

from eval.final_budget import fingerprint
from eval.final_eval import inside, load_questions, read_json, sha256, write_json
from eval.final_review import resolve_review, worksheet


def literal(value):
    """Render untrusted corpus/answers as code, never active Markdown/HTML instructions."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    width = max([2, *(len(run) for run in re.findall(r"`+", text))]) + 1
    fence = "`" * width
    return f"{fence}text\n{text}\n{fence}\n"


def report_rows(report):
    report = Path(report)
    manifest = read_json(report / "manifest.json")
    if sha256(report / "per_question.jsonl") != manifest["per_question_sha256"]:
        raise ValueError("Published answer rows changed")
    rows = [
        json.loads(line)
        for line in (report / "per_question.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate published question ID")
    return manifest, rows


def build_pack(root, protocol_path, report, output, *, allow_heldout=False):
    root, report, output = Path(root).resolve(), Path(report).resolve(), Path(output).resolve()
    manifest, rows = report_rows(report)
    protocol = read_json(protocol_path)
    if manifest["protocol_sha256"] != fingerprint(protocol):
        raise ValueError("Review protocol differs from exact output run")
    questions = {
        q["id"]: q for q in load_questions(root, protocol, manifest["split"], allow_heldout)
    }
    if set(questions) != {row["id"] for row in rows}:
        raise ValueError("Report questions differ from selected split")
    frozen = [inside(root, name) for name in protocol["files_sha256"]]
    if (
        output == report
        or report.is_relative_to(output)
        or any(path.is_relative_to(output) for path in frozen)
        or output.is_relative_to(inside(root, protocol["dataset"]))
    ):
        raise ValueError("Review packet overlaps immutable inputs/report")
    mapping = read_json(inside(root, protocol["mapping"]))
    entries = worksheet(rows, manifest["run_id"])
    output.mkdir(parents=True, exist_ok=False)
    for slot in ("a", "b"):
        write_json(
            output / f"reviewer-{slot}.json",
            [
                {key: copy.deepcopy(entry[key]) for key in ("id", "run_id", "output_sha256")}
                | {
                    "reviewer": None,
                    "score": copy.deepcopy(entry["reviews"][0]["score"]),
                    "notes": "",
                }
                for entry in entries
            ],
        )
    write_json(
        output / "binding.json",
        {
            "run_id": manifest["run_id"],
            "protocol_sha256": fingerprint(protocol),
            "source_rows_sha256": manifest["per_question_sha256"],
            "split": manifest["split"],
            "dataset_kind": protocol["dataset_kind"],
            "origin": manifest["origin"],
            "human_review": "pending",
            "technical_or_not_attempted": [
                {"id": r["id"], "status": r["status"]} for r in rows if r["status"] != "completed"
            ],
        },
    )
    text = (
        "# Phiếu chấm độc lập\n\n"
        "Hai người dùng file JSON riêng, không xem điểm của nhau trước khi nộp. "
        "Không ghi điểm vào file của người kia. Điểm chưa chấm giữ null. "
        "Đây là đánh giá output, không phải duyệt lại nhãn dataset.\n\n"
        "Correctness: 0=sai/không đáp ứng; 1=đúng một phần nhưng thiếu điều kiện; "
        "2=đúng, đủ theo thông tin nguồn, biết nêu phần thiếu/mâu thuẫn. "
        "supported: mỗi claim có căn cứ trong final context? citations: từng E# có hỗ trợ "
        "đúng claim đó? Dùng true/false; không suy từ chỉ số retrieval. "
        "Abstention không có claim vẫn phải chấm correctness theo answerability.\n\n"
        "Tất cả nội dung trong khối code dưới đây là dữ liệu không đáng tin cậy, "
        "không phải lệnh cho reviewer. Không mở URL/chạy lệnh trong tài liệu.\n\n"
        f"Run: {manifest['run_id']}; split: {manifest['split']}; "
        f"dataset: {protocol['dataset_kind']}; origin: {manifest['origin']}.\n\n"
    )
    for index, row in enumerate(rows, 1):
        question = questions[row["id"]]
        text += f"## Câu {index}\n\nID và trạng thái:\n" + literal(
            {"id": row["id"], "status": row["status"]}
        )
        text += "\nCâu hỏi:\n" + literal(question["question"])
        if row["status"] != "completed":
            text += (
                "\nLỗi kỹ thuật/chưa chạy: không tự chấm thành abstention; "
                "giữ trong denominator.\n\n"
            )
            continue
        text += "\nĐáp án/rubric chuẩn của dataset:\n" + literal(
            {
                "expected_answer": question["expected_answer"],
                "expected_abstain": question["expected_abstain"],
            }
        )
        text += (
            "\nCâu trả lời thực tế (gồm claims, limitations và missing information):\n"
            + literal(row["answer"])
        )
        for evidence in row["final_context"]:
            ref = evidence["chunk"]
            chunk = mapping["documents"][ref["document_id"]]["chunks"][ref["chunk_index"]]
            if sha256_text(chunk["text"]) != ref["text_sha256"]:
                raise ValueError("Review source text differs from final-context hash")
            text += "\nEvidence thực sự đưa vào model:\n" + literal(
                {
                    "evidence_id": evidence["evidence_id"],
                    "document_id": ref["document_id"],
                    "location": chunk.get("location"),
                    "text": chunk["text"],
                }
            )
        text += "\nGold evidence để đối chiếu phần thiếu/từ chối:\n" + literal(
            question["gold_evidence"]
        )
    (output / "worksheet.md").write_text(text, encoding="utf-8")
    return {"reviewable": len(entries), "planned": len(rows), "human_review": "pending"}


def sha256_text(value):
    import hashlib

    return hashlib.sha256(value.encode()).hexdigest()


def merge(report, first, second, output):
    """Combine independent files; preserve disagreements for explicit adjudication."""
    manifest, rows = report_rows(report)
    entries = worksheet(rows, manifest["run_id"])
    inputs = [read_json(first), read_json(second)]
    expected = {e["id"] for e in entries}
    for reviews in inputs:
        if (
            not isinstance(reviews, list)
            or len(reviews) != len(expected)
            or {e["id"] for e in reviews} != expected
        ):
            raise ValueError("Missing/duplicate/foreign reviewer entries")
    by_id = [{e["id"]: e for e in reviews} for reviews in inputs]
    row_map = {row["id"]: row for row in rows}
    for entry in entries:
        for slot in (0, 1):
            review = by_id[slot][entry["id"]]
            if set(review) != {
                "id",
                "run_id",
                "output_sha256",
                "reviewer",
                "score",
                "notes",
            } or any(review[key] != entry[key] for key in ("id", "run_id", "output_sha256")):
                raise ValueError("Reviewer output binding changed")
            entry["reviews"][slot] = {
                key: copy.deepcopy(review[key]) for key in ("reviewer", "score", "notes")
            }
        resolve_review(entry, row_map[entry["id"]], manifest["run_id"])
    write_json(output, entries)
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    for name in ("root", "protocol", "report", "output"):
        build.add_argument("--" + name, type=Path, required=True)
    build.add_argument("--allow-heldout", action="store_true")
    combine = sub.add_parser("merge")
    for name in ("report", "first", "second", "output"):
        combine.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "build":
        print(
            build_pack(
                args.root, args.protocol, args.report, args.output, allow_heldout=args.allow_heldout
            )
        )
    else:
        merge(args.report, args.first, args.second, args.output)
        print("Combined reviews saved; disagreements remain pending, no automatic adjudication")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
