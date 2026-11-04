"""Idempotent document cleanup with leases; external I/O stays outside DB locks."""

import logging
import re

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from app.models import Chunk, Document, DocumentRevision, ProcessingJob, SourceBlock
from app.services.jobs import JobQueue
from app.services.privacy import redact_document
from app.services.vectors import QdrantIndex
from app.services.worker_errors import LeaseLost, WorkerError

logger = logging.getLogger(__name__)


class CleanupQueue(JobQueue):
    kind = "cleanup"

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
                        Document.status == "deleted",
                    )
                )
                is not None
            )

    def finish(self, attempt):
        with self.sessions() as db:
            document, job, now = self.locked(db, attempt)
            redact_document(db, document)
            revisions = db.scalars(
                select(DocumentRevision).where(DocumentRevision.document_id == document.id)
            ).all()
            ids = [row.id for row in revisions]
            db.execute(delete(Chunk).where(Chunk.revision_id.in_(ids)))
            db.execute(delete(SourceBlock).where(SourceBlock.revision_id.in_(ids)))
            for revision in revisions:
                revision.status, revision.storage_key, revision.expected_chunk_count = (
                    "retired",
                    "",
                    0,
                )
            document.status, document.filename, document.mime, document.size_bytes = (
                "deleted",
                "[deleted]",
                "application/octet-stream",
                0,
            )
            document.active_revision_id = document.active_generation_id = None
            document.warnings_json = []
            job.status, job.finished_at = "completed", now
            job.lease_token = job.lease_expires_at = job.next_retry_at = None
            job.error_code, job.error_message, job.retryable = None, None, False
            db.commit()


class CleanupWorker:
    def __init__(self, queue, vector, stop=None):
        self.queue, self.vector, self.stop = queue, vector, stop

    def _vectors(self, workspace_id, document_id, collections, check=lambda: None):
        for collection in sorted(
            {name for name in collections if name and name != "pending"} | {self.vector.collection}
        ):
            check()
            vector = (
                self.vector
                if collection == self.vector.collection
                else QdrantIndex(
                    self.queue.settings.qdrant_url,
                    collection,
                    self.queue.settings.vector_timeout_seconds,
                )
            )
            try:
                vector.delete_document(workspace_id, document_id)
            finally:
                if vector is not self.vector:
                    vector.close()

    def _remove_file(self, key, workspace_id):
        if not key:
            return
        root = self.queue.settings.storage_dir.resolve()
        if not re.fullmatch(workspace_id.hex + r"/[0-9a-f]{32}\.(pdf|docx|txt|md)", key):
            raise WorkerError("storage_key_invalid")
        raw = root / key
        path = raw.resolve()
        if (
            not path.is_relative_to(root)
            or raw.is_symlink()
            or raw.parent.is_symlink()
            or getattr(raw.parent, "is_junction", lambda: False)()
        ):
            raise WorkerError("storage_key_invalid")
        try:
            path.unlink(missing_ok=True)
        except OSError:
            raise WorkerError("file_cleanup_failed", True) from None

    def run_once(self):
        from app.worker import Heartbeat

        attempt = self.queue.claim()
        if attempt is None:
            return None
        try:
            with Heartbeat(self.queue, attempt) as heartbeat:

                def check():
                    if heartbeat.lost.is_set():
                        raise LeaseLost()
                    if self.stop is not None and self.stop.is_set():
                        raise WorkerError("worker_shutdown", True)
                    self.queue.touch(attempt, "cleanup")

                check()
                with self.queue.sessions() as db:
                    revisions = db.execute(
                        select(
                            DocumentRevision.storage_key, DocumentRevision.collection_name
                        ).where(DocumentRevision.document_id == attempt.document_id)
                    ).all()
                self._vectors(
                    attempt.workspace_id,
                    attempt.document_id,
                    [row.collection_name for row in revisions],
                    check,
                )
                for row in revisions:
                    check()
                    self._remove_file(row.storage_key, attempt.workspace_id)
                check()
                self.queue.finish(attempt)
            result = {"job_id": str(attempt.job_id), "status": "completed"}
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
                    exc
                    if isinstance(exc, WorkerError)
                    else WorkerError("database_unavailable", True)
                    if isinstance(exc, SQLAlchemyError)
                    else WorkerError("cleanup_failed", True)
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
                result = {"job_id": str(attempt.job_id), "status": "recovery_pending"}
        logger.info("cleanup job_id=%s result=%s", attempt.job_id, result["status"])
        return result

    def reconcile_deleted(self):
        # Repeated scoped deletes collect late upserts even after the original job completed.
        with self.queue.sessions() as db:
            rows = db.execute(
                select(Document.id, Document.workspace_id, DocumentRevision.collection_name)
                .outerjoin(DocumentRevision, DocumentRevision.document_id == Document.id)
                .where(Document.status == "deleted")
            ).all()
        documents = {}
        for row in rows:
            documents.setdefault((row.id, row.workspace_id), []).append(row.collection_name)
        for (document_id, workspace_id), collections in documents.items():
            self._vectors(workspace_id, document_id, collections)
        return len(documents)
