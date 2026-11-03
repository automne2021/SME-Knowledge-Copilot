"""Short PostgreSQL transactions, document-before-job locking and fenced generations."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, or_, select

from app.models import Chunk, Document, DocumentRevision, ProcessingJob, SourceBlock
from app.services.embeddings import content_hash
from app.services.worker_errors import LeaseLost, WorkerError


@dataclass(frozen=True)
class Attempt:
    job_id: uuid.UUID
    document_id: uuid.UUID
    revision_id: uuid.UUID
    workspace_id: uuid.UUID
    generation_id: uuid.UUID
    lease_token: uuid.UUID
    lifecycle_version: int
    storage_key: str
    sha256: str
    mime: str
    started_epoch: float


class JobQueue:
    def __init__(self, sessions, settings):
        self.sessions, self.settings = sessions, settings

    @staticmethod
    def _now(db):
        return db.scalar(select(func.clock_timestamp()))

    def claim(self):
        with self.sessions() as db:
            now = self._now(db)
            eligible = (
                ProcessingJob.kind == "ingest",
                ProcessingJob.status.in_(["queued", "retry_wait"]),
                or_(ProcessingJob.next_retry_at.is_(None), ProcessingJob.next_retry_at <= now),
            )
            document = db.scalar(
                select(Document)
                .join(ProcessingJob, ProcessingJob.document_id == Document.id)
                .where(*eligible, Document.status.in_(["queued", "processing"]))
                .order_by(ProcessingJob.created_at, ProcessingJob.id)
                .limit(1)
                .with_for_update(of=Document, skip_locked=True)
            )
            if document is None:
                return None
            job = db.scalar(
                select(ProcessingJob)
                .where(*eligible, ProcessingJob.document_id == document.id)
                .with_for_update(skip_locked=True)
            )
            if job is None:
                return None
            revision = db.get(DocumentRevision, job.revision_id)
            if revision is None or job.attempts >= self.settings.job_max_attempts:
                job.status, job.error_code, job.finished_at = (
                    "failed",
                    "job_attempts_exhausted",
                    now,
                )
                document.status = "failed"
                db.commit()
                return None
            job.status, job.stage = "running", "validate"
            job.attempts += 1
            job.lease_token, job.generation_id = uuid.uuid4(), uuid.uuid4()
            job.lease_expires_at = now + timedelta(seconds=self.settings.job_lease_seconds)
            job.started_at, job.finished_at, job.next_retry_at = now, None, None
            job.error_code, job.error_message, job.retryable = None, None, False
            job.attempt_manifest_json = {}
            document.status, revision.status = "processing", "staging"
            attempt = Attempt(
                job.id,
                document.id,
                revision.id,
                document.workspace_id,
                job.generation_id,
                job.lease_token,
                document.lifecycle_version,
                revision.storage_key,
                document.sha256,
                document.mime,
                now.timestamp(),
            )
            db.commit()
            return attempt

    def locked(self, db, attempt):
        document = db.scalar(
            select(Document).where(Document.id == attempt.document_id).with_for_update()
        )
        job = db.scalar(
            select(ProcessingJob).where(ProcessingJob.id == attempt.job_id).with_for_update()
        )
        now = self._now(db)
        if (
            document is None
            or job is None
            or job.status != "running"
            or job.lease_token != attempt.lease_token
            or job.generation_id != attempt.generation_id
            or job.lease_expires_at is None
            or job.lease_expires_at <= now
            or job.revision_id != attempt.revision_id
            or document.status != "processing"
            or document.lifecycle_version != attempt.lifecycle_version
        ):
            raise LeaseLost()
        return document, job, now

    def touch(self, attempt, stage=None, completed=None, total=None):
        with self.sessions() as db:
            _, job, now = self.locked(db, attempt)
            job.lease_expires_at = now + timedelta(seconds=self.settings.job_lease_seconds)
            if stage:
                job.stage = stage
            if completed is not None:
                job.attempt_manifest_json = {
                    **job.attempt_manifest_json,
                    "progress": {
                        "completed_units": completed,
                        "total_units": total,
                        "unit": "chunks",
                    },
                }
            db.commit()

    def persist(self, attempt, parsed, chunks, profile):
        block_ids = {
            block.block_id: uuid.uuid5(attempt.generation_id, "block:" + block.block_id)
            for block in parsed.blocks
        }
        points = []
        with self.sessions() as db:
            document, job, _ = self.locked(db, attempt)
            revision = db.get(DocumentRevision, attempt.revision_id)
            if revision.status != "staging" or parsed.parser_version != profile["parser_version"]:
                raise WorkerError("index_configuration_mismatch")
            for index, block in enumerate(parsed.blocks):
                db.add(
                    SourceBlock(
                        id=block_ids[block.block_id],
                        revision_id=revision.id,
                        generation_id=attempt.generation_id,
                        block_index=index,
                        raw_text=block.raw_text,
                        normalized_text=block.normalized_text,
                        location_json={
                            **block.location,
                            "parser_block_id": block.block_id,
                            "context_block_ids": [
                                str(block_ids[item]) for item in block.context_ids
                            ],
                        },
                    )
                )
            for chunk in chunks:
                chunk_id = uuid.uuid5(
                    attempt.generation_id, f"chunk:{chunk.chunk_index}:{chunk.text_sha256}"
                )
                point_id = uuid.uuid5(attempt.generation_id, "point:" + str(chunk_id))
                spans = [
                    {**span, "block_id": str(block_ids[span["block_id"]])}
                    for span in chunk.source_spans
                ]
                db.add(
                    Chunk(
                        id=chunk_id,
                        revision_id=revision.id,
                        generation_id=attempt.generation_id,
                        chunk_index=chunk.chunk_index,
                        text=chunk.text,
                        text_sha256=chunk.text_sha256,
                        location_json=chunk.location,
                        source_spans_json=spans,
                        vector_point_id=point_id,
                        token_count=chunk.token_count,
                    )
                )
                points.append(
                    {
                        "id": str(point_id),
                        "payload": {
                            "workspace_id": str(attempt.workspace_id),
                            "document_id": str(document.id),
                            "revision_id": str(revision.id),
                            "generation_id": str(attempt.generation_id),
                            "chunk_id": str(chunk_id),
                            "index_version": profile["index_version"],
                            "attempt_started_epoch": attempt.started_epoch,
                        },
                    }
                )
            if not points:
                raise WorkerError("no_extractable_text")
            identity = {
                "generation_id": str(attempt.generation_id),
                "index_version": profile["index_version"],
                "collection_name": profile["collection_name"],
                "point_ids": sorted(point["id"] for point in points),
                "expected_count": len(points),
            }
            job.attempt_manifest_json = {"identity": identity, "sha256": content_hash(identity)}
            revision.parser_version = parsed.parser_version
            revision.chunking_config = profile["chunking_config"]
            revision.embedding_fingerprint = profile["embedding_fingerprint"]
            revision.index_version = profile["index_version"]
            revision.collection_name = profile["collection_name"]
            revision.expected_chunk_count = len(points)
            document.warnings_json = parsed.warnings
            db.commit()
        return points, identity

    def publish(self, attempt, identity, timings):
        with self.sessions() as db:
            document, job, now = self.locked(db, attempt)
            manifest = job.attempt_manifest_json
            if manifest.get("identity") != identity or manifest.get("sha256") != content_hash(
                identity
            ):
                raise WorkerError("sql_manifest_mismatch")
            actual = db.scalars(
                select(Chunk.vector_point_id).where(
                    Chunk.revision_id == attempt.revision_id,
                    Chunk.generation_id == attempt.generation_id,
                )
            ).all()
            if (
                sorted(str(item) for item in actual) != identity["point_ids"]
                or len(actual) != identity["expected_count"]
            ):
                raise WorkerError("sql_manifest_mismatch")
            revision = db.get(DocumentRevision, attempt.revision_id)
            if (
                revision.status != "staging"
                or revision.index_version != identity["index_version"]
                or revision.collection_name != identity["collection_name"]
                or revision.expected_chunk_count != len(actual)
            ):
                raise WorkerError("sql_manifest_mismatch")
            revision.status = "ready"
            document.active_revision_id, document.active_generation_id = (
                revision.id,
                attempt.generation_id,
            )
            document.status = "ready"
            job.status, job.stage, job.finished_at = "completed", "publish", now
            job.lease_token, job.lease_expires_at = None, None
            job.error_code, job.retryable = None, False
            job.attempt_manifest_json = {
                **manifest,
                "timings_ms": timings,
                "progress": {
                    "completed_units": len(actual),
                    "total_units": len(actual),
                    "unit": "chunks",
                },
            }
            db.commit()

    def is_completed(self, attempt):
        with self.sessions() as db:
            return (
                db.scalar(
                    select(ProcessingJob.id)
                    .join(Document, Document.id == ProcessingJob.document_id)
                    .where(
                        ProcessingJob.id == attempt.job_id,
                        ProcessingJob.status == "completed",
                        ProcessingJob.generation_id == attempt.generation_id,
                        Document.status == "ready",
                        Document.active_revision_id == attempt.revision_id,
                        Document.active_generation_id == attempt.generation_id,
                    )
                )
                is not None
            )

    def _fail_locked(self, db, document, job, now, error):
        job.error_code, job.error_message, job.retryable = error.code, None, error.retryable
        job.lease_token, job.lease_expires_at = None, None
        if error.retryable and job.attempts < self.settings.job_max_attempts:
            delay = min(
                self.settings.job_backoff_cap_seconds,
                self.settings.job_backoff_seconds * 2 ** max(0, job.attempts - 1),
            )
            job.status = "retry_wait"
            job.next_retry_at = now + timedelta(seconds=random.uniform(delay / 2, delay))
        else:
            job.status, job.finished_at, job.next_retry_at = "failed", now, None
            document.status = "needs_ocr" if error.code == "needs_ocr" else "failed"
            if job.revision_id:
                db.get(DocumentRevision, job.revision_id).status = "failed"

    def fail(self, attempt, error):
        with self.sessions() as db:
            document, job, now = self.locked(db, attempt)
            self._fail_locked(db, document, job, now, error)
            db.commit()

    def recover_expired(self):
        recovered = 0
        with self.sessions() as db:
            ids = db.execute(
                select(ProcessingJob.id, ProcessingJob.document_id)
                .where(
                    ProcessingJob.kind == "ingest",
                    ProcessingJob.status == "running",
                    ProcessingJob.lease_expires_at <= func.clock_timestamp(),
                )
                .limit(100)
            ).all()
        for job_id, document_id in ids:
            with self.sessions() as db:
                document = db.scalar(
                    select(Document)
                    .where(Document.id == document_id)
                    .with_for_update(skip_locked=True)
                )
                if document is None:
                    continue
                job = db.scalar(
                    select(ProcessingJob)
                    .where(ProcessingJob.id == job_id)
                    .with_for_update(skip_locked=True)
                )
                now = self._now(db)
                if job is None or job.status != "running" or job.lease_expires_at > now:
                    continue
                if document.status in {"deleting", "deleted"}:
                    job.status, job.finished_at = "cancelled", now
                    job.lease_token, job.lease_expires_at = None, None
                else:
                    self._fail_locked(db, document, job, now, WorkerError("lease_expired", True))
                db.commit()
                recovered += 1
        return recovered
