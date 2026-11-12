"""Temporary synthetic inputs shared by AT-R14 unit/SQL tests; no real model or dataset."""

import json
from pathlib import Path
from types import SimpleNamespace

from app.services.answering import PROMPT_VERSION
from app.services.chunking import split_document
from app.services.parsing import ParseLimits, _parse_inline
from eval import adversarial_eval as adv
from eval.final_eval import read_json
from eval.final_pacing import POLICY


class Counter:
    def count(self, text):
        return len(text) + 4

    count_query = count


def inputs(tmp_path, monkeypatch, settings, profile):
    cfg = {
        "model": settings.embedding_model,
        "revision": settings.embedding_revision,
        "dimension": settings.embedding_dimension,
        "candidate_k": settings.retrieval_candidate_k,
        "production_top_k": settings.retrieval_top_k,
        "evaluation_top_k": 10,
        "score_threshold": settings.retrieval_score_threshold,
        "prompt_version": PROMPT_VERSION,
        "expected_index_version": profile["index_version"],
        "request_pacing": POLICY,
    }
    for k in (
        "llm_model",
        "llm_base_url",
        "llm_evidence_budget_tokens",
        "llm_max_output_tokens",
        "llm_safety_margin_tokens",
        "llm_context_window_tokens",
        "llm_call_timeout_seconds",
        "chunk_size_tokens",
        "chunk_overlap_tokens",
        "query_timeout_seconds",
    ):
        cfg[k] = getattr(settings, k)
    for name in (
        adv.BASELINE,
        adv.BOOTSTRAP,
        "eval/adversarial_eval.py",
        "backend/app/placeholder.py",
    ):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(cfg) if name == adv.BASELINE else "# temporary fixture\n", encoding="utf-8"
        )
    counter = Counter()
    monkeypatch.setattr(adv, "runtime", lambda root: (settings, profile, counter, None))

    def prepare(path, kind, config, counts):
        parsed = _parse_inline(Path(path), kind, ParseLimits())
        return parsed, split_document(parsed, counts)

    monkeypatch.setattr("app.services.ingestion.prepare_document", prepare)
    plan = adv.prepare(tmp_path)
    output = tmp_path / adv.OUTPUT
    return SimpleNamespace(
        root=tmp_path,
        output=output,
        settings=settings,
        profile=profile,
        counter=counter,
        plan=plan,
        protocol=read_json(output / "protocol.json"),
    )
