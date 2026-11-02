"""Hand-calculated cases; these test metric arithmetic, not model quality."""

import pytest

from eval.metrics import abstention_scores, retrieval_scores


def test_hit_is_not_multi_evidence_recall():
    assert retrieval_scores({"a", "b"}, [{"a"}]) == {
        "hit": 1,
        "recall": 0.5,
        "mrr": 1.0,
        "all_evidence": 0,
    }


def test_overlapping_duplicate_hits_cannot_inflate_recall():
    result = retrieval_scores({"a", "b"}, [{"a"}, {"a"}, {"b"}])
    assert result["recall"] == 1
    assert result["all_evidence"] == 1


def test_rank_cutoff_and_first_relevant_rank():
    hits = [{"noise"}, set(), {"a"}, {"b"}]
    assert retrieval_scores({"a", "b"}, hits, k=2)["hit"] == 0
    result = retrieval_scores({"a", "b"}, hits, k=3)
    assert result["mrr"] == pytest.approx(1 / 3)
    assert result["recall"] == 0.5


def test_no_gold_groups_are_excluded_not_scored_zero():
    assert all(value is None for value in retrieval_scores(set(), [{"a"}]).values())


@pytest.mark.parametrize("k", [0, -1, True, 1.5])
def test_reject_invalid_k(k):
    with pytest.raises(ValueError, match="positive integer"):
        retrieval_scores({"a"}, [], k)


def test_abstention_precision_recall_and_false_abstention():
    # TP=1, FP=1, FN=1, TN=2; answerable denominator is 3.
    result = abstention_scores([True, True, False, False, False], [True, False, True, False, False])
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["false_abstention_rate"] == pytest.approx(1 / 3)


def test_undefined_abstention_denominators_are_null():
    assert abstention_scores([], []) == {
        "precision": None,
        "recall": None,
        "false_abstention_rate": None,
    }
    assert abstention_scores([False], [False])["recall"] is None
    assert abstention_scores([True], [True])["false_abstention_rate"] is None


def test_mismatched_samples_are_rejected():
    with pytest.raises(ValueError, match="lengths differ"):
        abstention_scores([True], [])


@pytest.mark.parametrize("prediction", ["timeout", None, 1])
def test_technical_errors_cannot_be_counted_as_abstention(prediction):
    with pytest.raises(ValueError, match="booleans"):
        abstention_scores([True], [prediction])
