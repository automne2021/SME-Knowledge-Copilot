"""Output-bound two-person human worksheets; never infer semantic scores from text."""

from __future__ import annotations

import copy

from eval.final_budget import fingerprint
from eval.metrics import abstention_scores


def answer_digest(row):
    return fingerprint({key: row[key] for key in ("id", "answer", "final_context")})


def empty_score(row):
    return {
        "correctness": None,
        "claims": [
            {"supported": None, "citations": dict.fromkeys(claim["evidence_ids"])}
            for claim in row["answer"]["claims"]
        ],
    }


def worksheet(rows, run_id):
    return [
        {
            "id": row["id"],
            "run_id": run_id,
            "output_sha256": answer_digest(row),
            "reviews": [
                {"reviewer": None, "score": empty_score(row), "notes": ""} for _ in range(2)
            ],
            "adjudication": None,
        }
        for row in rows
        if row["status"] == "completed"
    ]


def _valid_score(score, row):
    if not isinstance(score, dict) or set(score) != {"correctness", "claims"}:
        raise ValueError("Invalid human score fields")
    correctness = score["correctness"]
    if correctness is not None and (type(correctness) is not int or correctness not in {0, 1, 2}):
        raise ValueError("Correctness must be 0/1/2 or pending")
    if not isinstance(score["claims"], list) or len(score["claims"]) != len(
        row["answer"]["claims"]
    ):
        raise ValueError("Claim count differs from published answer")
    flags = []
    for judgement, claim in zip(score["claims"], row["answer"]["claims"], strict=True):
        if not isinstance(judgement, dict) or set(judgement) != {"supported", "citations"}:
            raise ValueError("Invalid claim review")
        if not isinstance(judgement["citations"], dict) or set(judgement["citations"]) != set(
            claim["evidence_ids"]
        ):
            raise ValueError("Citation identities differ from published answer")
        flags += [judgement["supported"], *judgement["citations"].values()]
    if any(flag is not None and type(flag) is not bool for flag in flags):
        raise ValueError("Support judgements must be booleans or pending")
    return correctness is not None and all(flag is not None for flag in flags)


def resolve_review(entry, row, run_id):
    if set(entry) != {"id", "run_id", "output_sha256", "reviews", "adjudication"}:
        raise ValueError("Invalid worksheet fields")
    if (entry["id"], entry["run_id"], entry["output_sha256"]) != (
        row["id"],
        run_id,
        answer_digest(row),
    ):
        raise ValueError("Worksheet does not belong to this exact output/run")
    reviews = entry["reviews"]
    if not isinstance(reviews, list) or len(reviews) != 2:
        raise ValueError("Two independent review slots required")
    complete, names = [], []
    for review in reviews:
        if not isinstance(review, dict) or set(review) != {"reviewer", "score", "notes"}:
            raise ValueError("Invalid review fields")
        name = review["reviewer"]
        if name is not None and (not isinstance(name, str) or not name.strip()):
            raise ValueError("Invalid reviewer identity")
        if not isinstance(review["notes"], str):
            raise ValueError("Review notes must be text")
        names.append(name.strip().casefold() if name else None)
        complete.append(_valid_score(review["score"], row) and bool(name))
    if names[0] and names[0] == names[1]:
        raise ValueError("Reviewers must be different people")
    if not all(complete):
        if entry["adjudication"] is not None:
            raise ValueError("Cannot adjudicate before both reviews are complete")
        return None
    if reviews[0]["score"] == reviews[1]["score"]:
        if entry["adjudication"] is not None:
            raise ValueError("Unnecessary adjudication on matching scores")
        return copy.deepcopy(reviews[0]["score"])
    decision = entry["adjudication"]
    if decision is None:
        return None
    if not isinstance(decision, dict) or set(decision) != {"score", "reason", "agreed_by"}:
        raise ValueError("Invalid adjudication")
    if not isinstance(decision["reason"], str) or not decision["reason"].strip():
        raise ValueError("Adjudication needs an explanation")
    agreed = decision["agreed_by"]
    if (
        not isinstance(agreed, list)
        or len(agreed) != 2
        or any(not isinstance(name, str) for name in agreed)
        or {name.strip().casefold() for name in agreed} != set(names)
    ):
        raise ValueError("Both original reviewers must agree to adjudication")
    if not _valid_score(decision["score"], row):
        raise ValueError("Adjudication must be complete")
    return copy.deepcopy(decision["score"])


def summarize(rows, entries, run_id):
    successful = {row["id"]: row for row in rows if row["status"] == "completed"}
    by_id = {}
    for entry in entries:
        if entry["id"] in by_id or entry["id"] not in successful:
            raise ValueError("Duplicate or foreign worksheet ID")
        by_id[entry["id"]] = entry
    resolved = {}
    for question_id, row in successful.items():
        if question_id in by_id:
            score = resolve_review(by_id[question_id], row, run_id)
            if score is not None:
                resolved[question_id] = score
    expected = [row["expected_abstain"] for row in successful.values()]
    predicted = [
        row["answer"]["answer_status"] == "insufficient_evidence" for row in successful.values()
    ]
    claims, links = [], []
    for score in resolved.values():
        claims += score["claims"]
        links += [flag for claim in score["claims"] for flag in claim["citations"].values()]
    pending = len(successful) - len(resolved)
    strict_passed = sum(score["correctness"] == 2 for score in resolved.values())
    return {
        "successful_answers": len(successful),
        "reviewed": len(resolved),
        "pending_or_disputed": pending,
        "all_successful_answers_reviewed": pending == 0,
        "correctness_mean_reviewed": (
            sum(score["correctness"] for score in resolved.values()) / len(resolved)
            if resolved
            else None
        ),
        "strict_success_numerator": strict_passed,
        "strict_success_denominator": len(rows),
        "strict_success_rate": strict_passed / len(rows) if rows and not pending else None,
        "faithfulness": sum(c["supported"] for c in claims) / len(claims) if claims else None,
        "factual_claim_count_reviewed": len(claims),
        "citation_correctness": sum(links) / len(links) if links else None,
        "citation_link_count_reviewed": len(links),
        "citation_completeness": (
            sum(any(c["citations"].values()) for c in claims) / len(claims) if claims else None
        ),
        "abstention_successful_only": abstention_scores(expected, predicted),
        "abstention_sample_count": len(expected),
    }
