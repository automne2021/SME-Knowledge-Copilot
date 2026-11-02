"""Metrics over already matched evidence groups; not a retrieval/model evaluator."""


def retrieval_scores(required: set[str], ranked_hits: list[set[str]], k: int = 5) -> dict:
    if type(k) is not int or k <= 0:
        raise ValueError("k must be a positive integer")
    if not required:
        return {"hit": None, "recall": None, "mrr": None, "all_evidence": None}
    found = set()
    reciprocal_rank = 0.0
    for rank, hits in enumerate(ranked_hits[:k], 1):
        relevant = required & hits
        if relevant and reciprocal_rank == 0:
            reciprocal_rank = 1 / rank
        found.update(relevant)
    return {
        "hit": int(bool(found)),
        "recall": len(found) / len(required),
        "mrr": reciprocal_rank,
        "all_evidence": int(found == required),
    }


def abstention_scores(expected: list[bool], predicted: list[bool]) -> dict:
    if len(expected) != len(predicted):
        raise ValueError("Expected and predicted lengths differ")
    if any(type(value) is not bool for value in expected + predicted):
        raise ValueError("Abstention decisions must be booleans, not technical error statuses")
    true_positive = sum(e and p for e, p in zip(expected, predicted, strict=True))
    positive = sum(predicted)
    unanswerable = sum(expected)
    answerable = len(expected) - unanswerable
    false_abstention = sum(not e and p for e, p in zip(expected, predicted, strict=True))
    return {
        "precision": true_positive / positive if positive else None,
        "recall": true_positive / unanswerable if unanswerable else None,
        "false_abstention_rate": false_abstention / answerable if answerable else None,
    }
