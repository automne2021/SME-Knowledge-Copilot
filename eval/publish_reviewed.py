"""Publish a verified human-reviewed copy, without editing the working draft or ledger."""

import argparse
import hashlib
import json
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from eval.build_dataset import json_bytes, put
from eval.validate_dataset import require, safe_path, validate

ROOT = Path(__file__).resolve().parent
REVIEWED = ROOT / "snapshots" / "reviewed-v1"


def publish(source: Path, output: Path) -> dict:
    require(not output.resolve().is_relative_to(source.resolve()), "Output must be outside draft")
    result = validate(source)
    require(result["human_approved"] == result["questions"], "Human review is incomplete")
    source_bytes = (source / "corpus_manifest.json").read_bytes()
    manifest = json.loads(source_bytes)
    manifest.update(
        dataset_version="reviewed-v1",
        label_status="human_reviewed",
        parent_dataset_version=manifest["dataset_version"],
        parent_manifest_sha256=hashlib.sha256(source_bytes).hexdigest(),
        human_review_sha256=hashlib.sha256((source / "human_review.csv").read_bytes()).hexdigest(),
    )
    names = [entry["path"] for entry in manifest["documents"] + manifest["fixtures"]]
    names += ["questions.jsonl", "source_blocks.json", "human_review.csv"]
    if output.exists():
        validate(output, require_reviewed=True)
        old = json.loads((output / "corpus_manifest.json").read_text(encoding="utf-8"))
        expected = {key: value for key, value in old.items() if key != "published_at"}
        require(expected == manifest, "Existing reviewed snapshot differs; use a new version")
        for name in names:
            require(
                safe_path(source, name).read_bytes() == safe_path(output, name).read_bytes(),
                "Existing reviewed artifact differs",
            )
        return validate(output, require_reviewed=True)
    manifest["published_at"] = datetime.now(UTC).isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Validate a complete staged copy before exposing the versioned output directory.
    # mkdir inherits workspace ACLs. Windows mkdtemp uses a private DACL that would
    # survive rename and prevent the user's normal process from reading the snapshot.
    staging = output.parent / f".{output.name}.staging-{uuid.uuid4().hex}"
    staging.mkdir()
    try:
        for name in names:
            destination = safe_path(staging, name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe_path(source, name), destination)
        put(staging / "corpus_manifest.json", json_bytes(manifest))
        result = validate(staging, require_reviewed=True)
        staging.rename(output)
    finally:
        if staging.exists():
            require(
                staging.resolve().parent == output.parent.resolve(),
                "Refusing cleanup outside the snapshot parent",
            )
            shutil.rmtree(staging)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "datasets")
    parser.add_argument("--output", type=Path, default=REVIEWED)
    args = parser.parse_args()
    print(json.dumps(publish(args.source, args.output), indent=2))
