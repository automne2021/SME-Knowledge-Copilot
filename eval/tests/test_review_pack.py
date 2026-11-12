"""Independent output-bound worksheets; fixtures only, no human scores invented."""

import pytest

from eval import review_pack
from eval.final_eval import read_json, run_replay, write_json
from eval.final_review import resolve_review
from eval.tests import test_final_eval as fixtures

frozen = fixtures.frozen
deny_network_and_project_corpus = fixtures.deny_network_and_project_corpus


@pytest.fixture
def packet(frozen):
    root, protocol_path, _, capture, *_ = frozen
    source = root / "capture.json"
    write_json(source, capture)
    report = root / "report"
    run_replay(root, protocol_path, source, report, "dev")
    output = root / "packet"
    result = review_pack.build_pack(root, protocol_path, report, output)
    return root, report, output, result


def test_packet_has_two_independent_blank_review_files_and_context(packet):
    _, report, output, result = packet
    assert result == {"reviewable": 3, "planned": 3, "human_review": "pending"}
    first, second = (read_json(output / name) for name in ("reviewer-a.json", "reviewer-b.json"))
    assert first == second
    assert all(e["reviewer"] is None and e["score"]["correctness"] is None for e in first)
    text = (output / "worksheet.md").read_text(encoding="utf-8")
    assert "Evidence thực sự đưa vào model" in text and "abcdefghij" in text
    assert "offline_fixture" in text
    assert read_json(report / "metrics.json")["human"]["reviewed"] == 0


def test_merge_preserves_disagreement_and_never_adjudicates(packet):
    root, report, output, _ = packet
    files = []
    for index, name in enumerate(("Alice", "Bob")):
        entries = read_json(output / "reviewer-a.json")
        for entry in entries:
            entry["reviewer"] = name
            entry["score"]["correctness"] = index + 1
            for claim in entry["score"]["claims"]:
                claim["supported"] = True
                claim["citations"] = dict.fromkeys(claim["citations"], True)
        path = root / (name + ".json")
        write_json(path, entries)
        files.append(path)
    combined = review_pack.merge(report, *files, root / "combined.json")
    manifest, rows = review_pack.report_rows(report)
    assert all(entry["adjudication"] is None for entry in combined)
    assert all(
        resolve_review(e, r, manifest["run_id"]) is None
        for e, r in zip(combined, rows, strict=True)
    )


@pytest.mark.parametrize(
    "change", ["same-reviewer", "digest", "run", "missing", "duplicate", "score"]
)
def test_invalid_reviews_cannot_be_accepted(packet, change):
    root, report, output, _ = packet
    first = read_json(output / "reviewer-a.json")
    second = read_json(output / "reviewer-b.json")
    for entry in first + second:
        entry["reviewer"] = "Alice"
    if change != "same-reviewer":
        for entry in second:
            entry["reviewer"] = "Bob"
    if change == "digest":
        second[0]["output_sha256"] = "0" * 64
    elif change == "run":
        second[0]["run_id"] = "another"
    elif change == "missing":
        second.pop()
    elif change == "duplicate":
        second[-1] = second[0]
    elif change == "score":
        second[0]["score"]["correctness"] = 99
    paths = [root / "first.json", root / "second.json"]
    for path, entries in zip(paths, (first, second), strict=True):
        write_json(path, entries)
    with pytest.raises(ValueError):
        review_pack.merge(report, *paths, root / "bad.json")
    assert not (root / "bad.json").exists()


def test_tampered_published_output_is_rejected(packet):
    root, report, _, _ = packet
    (report / "per_question.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="rows changed"):
        review_pack.build_pack(root, root / "protocol.json", report, root / "new-packet")


def test_literal_text_cannot_close_fence_or_render_script_links():
    text = "```\n<script>alert(1)</script>\n![leak](https://example.invalid)\n````"
    escaped = review_pack.literal(text)
    assert escaped.startswith("`````text\n") and escaped.endswith("\n`````\n")


def test_review_builder_cannot_open_heldout_without_explicit_flag(frozen):
    root, protocol_path, _, _, *_ = frozen
    # Reject before held-out text is selected, even if a caller changes report split metadata.
    report = root / "report"
    report.mkdir()
    (report / "per_question.jsonl").write_text("", encoding="utf-8")
    from eval.final_budget import fingerprint
    from eval.final_eval import sha256

    write_json(
        report / "manifest.json",
        {
            "per_question_sha256": sha256(report / "per_question.jsonl"),
            "protocol_sha256": fingerprint(read_json(protocol_path)),
            "split": "test",
        },
    )
    with pytest.raises(ValueError, match="Held-out"):
        review_pack.build_pack(root, protocol_path, report, root / "no-test-review")
