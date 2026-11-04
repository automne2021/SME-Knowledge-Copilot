"""Standalone ingestion worker. Start from backend/: python -B -m app.worker."""

from __future__ import annotations

import argparse
import hashlib
import logging
import signal
import threading
import time

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.services.chunking import E5TokenCounter
from app.services.embeddings import LocalEmbedder, frozen_profile, validate_vectors
from app.services.ingestion import prepare_document
from app.services.jobs import JobQueue
from app.services.orphans import OrphanCleaner
from app.services.parsing import ParseError
from app.services.uploads import MIMES
from app.services.vectors import QdrantIndex
from app.services.worker_errors import LeaseLost, WorkerError

logger = logging.getLogger(__name__)


class Heartbeat:
    def __init__(self, queue, attempt):
        self.queue, self.attempt = queue, attempt
        self.stop = threading.Event()
        self.lost = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True, name="ingestion-heartbeat")

    def _run(self):
        while not self.stop.wait(self.queue.settings.job_heartbeat_seconds):
            try:
                self.queue.touch(self.attempt)
            except Exception:
                self.lost.set()
                return

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join(timeout=10)


class IngestionWorker:
    def __init__(self, queue, vector, embedder, counter, profile, stop=None):
        self.queue, self.vector, self.embedder, self.counter, self.profile = (
            queue,
            vector,
            embedder,
            counter,
            profile,
        )
        self.stop = stop or threading.Event()

    def run_once(self):
        attempt = self.queue.claim()
        if attempt is None:
            return None
        started = time.perf_counter()
        timings = {}
        try:
            with Heartbeat(self.queue, attempt) as heartbeat:

                def check(stage, done=None, total=None):
                    if heartbeat.lost.is_set():
                        raise LeaseLost()
                    if self.stop.is_set():
                        raise WorkerError("worker_shutdown", True)
                    self.queue.touch(attempt, stage, done, total)

                check("validate")
                root = self.queue.settings.storage_dir.resolve()
                path = (root / attempt.storage_key).resolve()
                if not path.is_relative_to(root) or not path.is_file():
                    raise WorkerError("source_file_missing")
                with path.open("rb") as stream:
                    if hashlib.file_digest(stream, "sha256").hexdigest() != attempt.sha256:
                        raise WorkerError("source_checksum_mismatch")
                check("parse")
                stage_start = time.perf_counter()
                file_format = next(
                    (kind for kind, mime in MIMES.items() if mime == attempt.mime), None
                )
                parsed, chunks = prepare_document(
                    path, file_format, self.queue.settings, self.counter
                )
                timings["parse_chunk_ms"] = round((time.perf_counter() - stage_start) * 1000, 3)
                check("chunk")
                points, identity = self.queue.persist(attempt, parsed, chunks, self.profile)
                embedding_ms = vector_ms = 0.0
                batch_size = self.queue.settings.embedding_batch_size
                for offset in range(0, len(chunks), batch_size):
                    check("embed", offset, len(chunks))
                    stage_start = time.perf_counter()
                    texts = [chunk.text for chunk in chunks[offset : offset + batch_size]]
                    vectors = self.embedder.encode(texts)
                    validate_vectors(vectors, len(texts))
                    embedding_ms += (time.perf_counter() - stage_start) * 1000
                    batch = [
                        {**point, "vector": vector}
                        for point, vector in zip(
                            points[offset : offset + batch_size], vectors, strict=True
                        )
                    ]
                    check("upsert", offset, len(chunks))
                    stage_start = time.perf_counter()
                    self.vector.upsert(batch)
                    vector_ms += (time.perf_counter() - stage_start) * 1000
                check("upsert", len(chunks), len(chunks))
                stage_start = time.perf_counter()
                self.vector.verify(
                    attempt.generation_id, {point["id"]: point["payload"] for point in points}
                )
                timings.update(
                    embedding_ms=round(embedding_ms, 3),
                    vector_upsert_ms=round(vector_ms, 3),
                    vector_verify_ms=round((time.perf_counter() - stage_start) * 1000, 3),
                )
                check("publish", len(chunks), len(chunks))
                timings["total_before_publish_ms"] = round(
                    (time.perf_counter() - started) * 1000, 3
                )
                self.queue.publish(attempt, identity, timings)
                result = {
                    "job_id": str(attempt.job_id),
                    "status": "completed",
                    "chunk_count": len(chunks),
                    "timings_ms": timings,
                }
        except Exception as exc:
            try:
                if self.queue.is_completed(attempt):
                    return {
                        "job_id": str(attempt.job_id),
                        "status": "completed",
                        "recovered_commit_ack": True,
                    }
                if isinstance(exc, LeaseLost):
                    return {"job_id": str(attempt.job_id), "status": "lease_lost"}
                error = (
                    WorkerError(exc.code)
                    if isinstance(exc, ParseError)
                    else exc
                    if isinstance(exc, WorkerError)
                    else WorkerError("database_unavailable", True)
                    if isinstance(exc, SQLAlchemyError)
                    else WorkerError("ingestion_failed")
                )
                self.queue.fail(attempt, error)
                result = {
                    "job_id": str(attempt.job_id),
                    "status": "error",
                    "error_code": error.code,
                    "retryable": error.retryable,
                }
            except LeaseLost:
                result = {"job_id": str(attempt.job_id), "status": "lease_lost"}
            except Exception:
                # DB may be down. Leave the lease recoverable, without overwriting uncertain state.
                result = {"job_id": str(attempt.job_id), "status": "recovery_pending"}
        logger.info("ingestion job_id=%s result=%s", attempt.job_id, result["status"])
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--once", action="store_true", help="Recover/sweep, process at most one job"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = get_settings()
    stop = threading.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda *_: stop.set())
    vector = embedder = None
    try:
        profile = frozen_profile(settings)
        vector = QdrantIndex(
            settings.qdrant_url, settings.qdrant_collection, settings.vector_timeout_seconds
        )
        vector.ensure_collection(profile["embedding_hash"])
        embedder = LocalEmbedder(profile, settings)
        queue = JobQueue(get_sessionmaker(), settings)
        worker = IngestionWorker(
            queue, vector, embedder, E5TokenCounter(settings.hf_home / "hub"), profile, stop
        )
        cleaner = OrphanCleaner(queue.sessions, settings, vector)
        swept = 0.0
        while not stop.is_set():
            try:
                queue.recover_expired()
                if time.monotonic() - swept >= settings.worker_sweep_seconds:
                    cleaner.sweep()
                    swept = time.monotonic()
                result = worker.run_once()
                if args.once:
                    break
                if result is None:
                    stop.wait(settings.worker_poll_seconds)
            except Exception as exc:
                logger.error("worker_poll_failed type=%s", type(exc).__name__)
                if args.once:
                    return 1
                stop.wait(settings.worker_poll_seconds)
        return 0
    except Exception as exc:
        logger.error("worker_startup_failed type=%s", type(exc).__name__)
        return 1
    finally:
        if embedder:
            embedder.close()
        if vector:
            vector.close()


if __name__ == "__main__":
    raise SystemExit(main())
