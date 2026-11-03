"""Exact metric math: alternatives, required multi-spans, overlap, technical failures."""

import pytest

from eval.metrics import retrieval_scores
from eval.span_metrics import aggregate, covered_chars, ranked_group_hits


def span(block="b1", start=0, end=10, **extra):
    return {"block_id": block, "char_start": start, "char_end": end, **extra}


def test_overlap_union_does_not_double_count_and_clips_boundaries():
    assert covered_chars([(-10, 4), (2, 5), (3, 6), (20, 30)], 0, 10) == 6
    assert covered_chars([(0, 3), (5, 10), (9, 12)], 0, 10) == 8


def test_group_completes_at_rank_that_union_reaches_eighty_percent():
    groups = {"G1": [[span()]]}
    ranks = ranked_group_hits(
        groups, [[span(end=4)], [span(start=2, end=6)], [span(start=5, end=8)]]
    )
    assert ranks == [set(), set(), {"G1"}]
    assert retrieval_scores({"G1"}, ranks, 3)["mrr"] == pytest.approx(1 / 3)
    assert retrieval_scores({"G1"}, ranks, 2)["recall"] == 0


def test_required_groups_and_alternative_quotes_are_distinct():
    groups = {"G1": [[span("a")], [span("b")]], "G2": [[span("c"), span("d")]]}
    ranks = ranked_group_hits(groups, [[span("b")], [span("c")], [span("d")]])
    assert ranks == [{"G1"}, set(), {"G2"}]
    assert retrieval_scores(set(groups), ranks, 1)["recall"] == 0.5
    assert retrieval_scores(set(groups), ranks, 2)["all_evidence"] == 0
    assert retrieval_scores(set(groups), ranks, 3)["all_evidence"] == 1


def test_context_duplicate_and_wrong_block_do_not_create_gold_hits():
    groups = {"G1": [[span()]]}
    assert ranked_group_hits(groups, [[span(role="context")], [span("wrong")]]) == [set(), set()]
    assert ranked_group_hits(groups, [[span(end=4)], [span(end=4)]]) == [set(), set()]


def test_technical_failures_stay_in_strict_denominator():
    rows = [
        {
            "required_groups": ["G1"],
            "status": "completed",
            "ranked_group_hits": [["G1"]],
            "latency_ms": 5,
        },
        {"required_groups": ["G2"], "status": "failed", "latency_ms": 10},
        {"required_groups": [], "status": "completed", "ranked_group_hits": [], "latency_ms": 7},
    ]
    result = aggregate(rows)
    assert result["successful_answerable"]["5"]["recall"] == 1
    assert result["strict_all_answerable"]["5"]["recall"] == 0.5
    assert result["technical_error_rate"] == pytest.approx(1 / 3)
    assert result["multi_evidence_successful"]["5"]["all_evidence"] is None
    assert result["latency_ms"]["p95_nearest_rank"] == 7


def test_empty_or_unanswerable_denominator_is_null():
    assert aggregate([])["successful_answerable"]["1"]["recall"] is None
    row = {"required_groups": [], "status": "completed", "latency_ms": 1, "ranked_group_hits": []}
    assert aggregate([row])["answerable_count"] == 0


def test_invalid_interval_and_failed_cached_hits_cannot_inflate_metrics():
    with pytest.raises(ValueError):
        covered_chars([(5, 1)], 0, 10)
    row = {
        "required_groups": ["G1"],
        "status": "failed",
        "latency_ms": 2,
        "ranked_group_hits": [["G1"]],
    }
    assert aggregate([row])["strict_all_answerable"]["5"]["recall"] == 0


@pytest.mark.parametrize("groups", [{"G1": []}, {"G1": [[]]}])
def test_empty_gold_is_not_silently_accepted(groups):
    with pytest.raises(ValueError):
        ranked_group_hits(groups, [])
