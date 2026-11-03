"""Versioned standalone model smoke reports. Never writes to DB or Qdrant."""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import threading
import time
import uuid
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from dotenv import dotenv_values

from eval.build_dataset import json_bytes, put
from eval.publish_reviewed import REVIEWED
from eval.validate_dataset import require, validate

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "configs/model_smoke.json"
FILES = [
    "config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentencepiece.bpe.model",
]


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


class MemorySampler:
    def __init__(self):
        import psutil

        self.process = psutil.Process()
        self.baseline = self.process.memory_info().rss
        self.peak = self.baseline
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def sample(self):
        while not self.stop.wait(0.02):
            self.peak = max(self.peak, self.process.memory_info().rss)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join()
        self.peak = max(self.peak, self.process.memory_info().rss)


def embedding_smoke(config: dict, download: bool) -> tuple[dict, list[dict]]:
    from huggingface_hub import snapshot_download

    from eval.embedding_runtime import E5Encoder, InputTooLong, check_lengths, prepare_inputs

    values = {**dotenv_values(ROOT.parent / ".env"), **os.environ}
    cache = Path(values.get("HF_HOME") or ROOT.parent / ".cache/huggingface") / "hub"
    started = time.perf_counter()
    snapshot = Path(
        snapshot_download(
            repo_id=config["model_id"],
            revision=config["revision"],
            allow_patterns=FILES,
            cache_dir=cache,
            local_files_only=not download,
            token=False,
        )
    )
    download_seconds = time.perf_counter() - started
    fingerprint = {name: digest(snapshot / name) for name in FILES}
    blocks = json.loads((REVIEWED / "source_blocks.json").read_text(encoding="utf-8"))
    # Compatibility only: no ranking, test questions, retrieval scores or tuning.
    passages = [f"{b['document_id']}\n{b['text']}" for b in blocks]
    questions = [
        json.loads(line)
        for line in (REVIEWED / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    dev = [q for q in questions if q["split"] == "dev"][:5]
    with MemorySampler() as memory:
        started = time.perf_counter()
        encoder = E5Encoder(snapshot, threads=config["threads"])
        load_seconds = time.perf_counter() - started
        torch = encoder.torch
        require(torch.version.cuda is None, "Expected CPU-only PyTorch wheel")
        started = time.perf_counter()
        first = encoder.encode([passages[0]], "passage")
        cold_seconds = time.perf_counter() - started
        started = time.perf_counter()
        vectors = encoder.encode(passages, "passage", config["batch_size"])
        encode_seconds = time.perf_counter() - started
        require(bool(torch.allclose(vectors[0], first[0], atol=1e-5)), "Batch/padding drift")
        norms = torch.linalg.vector_norm(vectors, dim=1)
        require(bool(torch.allclose(norms, torch.ones_like(norms), atol=1e-5)), "Bad L2 norms")
        rows = []
        for question in dev:
            started = time.perf_counter()
            encoder.encode([question["question"]], "query")
            rows.append(
                {"id": question["id"], "kind": "query", "seconds": time.perf_counter() - started}
            )
        prefix = "passage: Quy định thử giới hạn\n"
        candidates = [prefix + "xin " * n for n in range(450, 530)]
        by_length = {
            len(encoder.tokenizer(text, truncation=False)["input_ids"]): text for text in candidates
        }
        require(512 in by_length and 513 in by_length, "Cannot construct boundary probes")
        require(check_lengths(encoder.tokenizer, [by_length[512]]) == [512], "Boundary count")
        encoder.encode([by_length[512].removeprefix("passage: ")], "passage")
        try:
            encoder.encode([by_length[513].removeprefix("passage: ")], "passage")
        except InputTooLong:
            overflow_rejected = True
        else:
            raise ValueError("Oversized input was not rejected")
        lengths = check_lengths(encoder.tokenizer, prepare_inputs(passages, "passage"))
        rows += [
            {"id": block["source_block_id"], "kind": "passage", "tokens": length}
            for block, length in zip(blocks, lengths, strict=True)
        ]
    return {
        "status": "passed",
        "stage": "embedding_compatibility",
        "model_id": config["model_id"],
        "revision": config["revision"],
        "files_sha256": fingerprint,
        "passages_encoded": len(passages),
        "queries_encoded": len(dev),
        "shape": list(vectors.shape),
        "dtype": str(vectors.dtype),
        "device": str(vectors.device),
        "finite": True,
        "l2_norm_min": norms.min().item(),
        "l2_norm_max": norms.max().item(),
        "max_observed_tokens": max(lengths),
        "boundary_512_encoded": True,
        "overflow_513_rejected": overflow_rejected,
        "batch_padding_consistent": True,
        "cache_or_download_seconds": download_seconds,
        "cold_model_load_seconds": load_seconds,
        "first_passage_encode_seconds": cold_seconds,
        "warm_passages_seconds": encode_seconds,
        "passages_per_second": len(passages) / encode_seconds,
        "process_rss_before_model_import_bytes": memory.baseline,
        "sampled_peak_process_rss_bytes": memory.peak,
        "sampling_interval_seconds": 0.02,
        "package_versions": {
            name: version(name)
            for name in ["torch", "transformers", "huggingface-hub", "psutil", "numpy"]
        },
        "retrieval_quality": "not_measured",
        "llm_calls": 0,
        "api_cost_usd": 0,
    }, rows


def llm_cases() -> list[dict]:
    questions = [
        json.loads(line)
        for line in (REVIEWED / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    cases = []
    for q in questions:
        if q["id"] not in {"q001", "q007", "q009", "q014"}:
            continue
        require(q["split"] == "dev", "LLM smoke must not tune on test questions")
        cases.append(
            {
                "id": q["id"],
                "question": q["question"],
                "evidence": [
                    {"evidence_id": item["evidence_id"], "text": item["quote"]}
                    for item in q["gold_evidence"]
                ],
            }
        )
    cases.append(
        {
            "id": "adhoc_conflict_not_human_gold",
            "question": "Có biết chính sách nào đang có hiệu lực không?",
            "evidence": [
                {"evidence_id": "E1", "text": "Bản A: 12 ngày phép, không ghi ngày hiệu lực."},
                {
                    "evidence_id": "E2",
                    "text": "Bản B: 15 ngày phép, không ghi ngày thay thế bản A.",
                },
            ],
        }
    )
    return cases


def llm_smoke(config: dict, case_id: str | None = None) -> tuple[dict, list[dict]]:
    import httpx

    from eval.gemini_smoke import SmokeProviderError, generate, preflight

    limit = config["max_calls"]
    require(type(limit) is int and 1 <= limit <= 5, "max_calls must be an integer from 1 to 5")
    cases = llm_cases()
    if case_id is not None:
        require(case_id in {case["id"] for case in cases}, "Unknown smoke case ID")
        cases = [case for case in cases if case["id"] == case_id]
    cases = cases[:limit]
    values = {**dotenv_values(ROOT.parent / ".env"), **os.environ}
    reasons = preflight(values)
    if reasons:
        return {
            "status": "not_run",
            "stage": "llm_compatibility",
            "reasons": reasons,
            "api_calls_attempted": 0,
            "api_cost_usd": 0,
        }, []
    rows = []
    with httpx.Client(trust_env=False, follow_redirects=False) as client:
        for case in cases:
            started = time.perf_counter()
            row = {"id": case["id"]}
            try:
                row.update(generate(values, case["question"], case["evidence"], client))
                row["status"] = "schema_and_ids_valid"
            except SmokeProviderError as exc:
                row.update(status="technical_error", error_code=str(exc))
                row.update(exc.metadata)
            row["seconds"] = time.perf_counter() - started
            rows.append(row)
            if row["status"] == "technical_error":
                break  # No retry/fallback or repeated quota failures.
    errors = sum(row["status"] == "technical_error" for row in rows)
    return {
        "status": "passed" if len(rows) == len(cases) and not errors else "failed",
        "stage": "llm_compatibility",
        "requested_case_ids": [case["id"] for case in cases],
        "api_calls_attempted": len(rows),
        "technical_errors": errors,
        "api_cost_usd": None,
        "billing_verification": "manual_free_tier_attestation",
        "semantic_correctness": "requires_human_scoring",
        "e2e_rag": "not_run",
    }, rows


def run(stage: str, output: Path, download: bool = False, case_id: str | None = None) -> dict:
    import psutil

    require(not output.exists(), "Report path exists; choose a new run directory")
    require(case_id is None or stage == "llm", "Case selection only applies to LLM smoke")
    validate(REVIEWED, require_reviewed=True)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest = {
        "run_id": output.name,
        "started_at_utc": datetime.now(UTC).isoformat(),
        "stage": stage,
        "selected_case_id": case_id,
        "dataset_manifest_sha256": digest(REVIEWED / "corpus_manifest.json"),
        "config_sha256": digest(CONFIG),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu_logical": psutil.cpu_count(),
        "memory_available_before_bytes": psutil.virtual_memory().available,
        "code_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT.parent, text=True
        ).strip(),
        "working_tree_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT.parent, text=True
            ).strip()
        ),
        "source_sha256": {
            name: digest(ROOT / name)
            for name in ["model_smoke.py", "embedding_runtime.py", "gemini_smoke.py"]
        },
        "test_questions_used_for_tuning": False,
    }
    # The shim alone no longer captures inference behavior after Step 06.
    shared_runtime = ROOT.parent / "backend/app/services/e5_runtime.py"
    manifest["source_sha256"]["backend_e5_runtime.py"] = digest(shared_runtime)
    output.mkdir(parents=True, exist_ok=False)
    put(output / "manifest.json", json_bytes(manifest))
    put(output / "config.json", json_bytes(config))
    for name in manifest["source_sha256"]:
        source = shared_runtime if name == "backend_e5_runtime.py" else ROOT / name
        put(output / "source_snapshot" / (name + ".txt"), source.read_bytes())
    try:
        result, rows = (
            embedding_smoke(config["embedding"], download)
            if stage == "embedding"
            else llm_smoke(config["llm"], case_id)
        )
    except Exception as exc:
        put(
            output / "metrics.json",
            json_bytes({"status": "failed", "error_type": type(exc).__name__}),
        )
        raise
    put(output / "metrics.json", json_bytes(result))
    put(
        output / "per_input.jsonl",
        b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows),
    )
    put(
        output / "report.md",
        (
            f"# Model smoke: {stage}\n\nStatus: **{result['status']}**.\n\n"
            "See metrics.json for measurements and manifest.json for fingerprints.\n\n"
            "Compatibility smoke run, not a RAG quality benchmark. Stub tests, real inference "
            "and human semantic review are separate evidence.\n"
        ).encode(),
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["embedding", "llm"])
    parser.add_argument("--download", action="store_true", help="Allow public model download")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case-id", help="Run exactly one named dev/adhoc smoke case")
    args = parser.parse_args()
    output = args.output or ROOT / "reports" / (
        f"smoke_{args.stage}_{datetime.now(UTC):%Y%m%dT%H%M%S}_{uuid.uuid4().hex[:8]}"
    )
    result = run(args.stage, output, args.download, args.case_id)
    print(json.dumps({"report": str(output), **result}, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 2)
