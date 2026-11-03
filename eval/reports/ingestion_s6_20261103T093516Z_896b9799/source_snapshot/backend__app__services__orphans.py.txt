"""Reconcile abandoned generations and old unreferenced canonical upload files."""

import re
import time
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select

from app.models import AnswerCitation, Chunk, Document, DocumentRevision, ProcessingJob, SourceBlock


class OrphanCleaner:
    def __init__(self, sessions, settings, vector):
        self.sessions, self.settings, self.vector = sessions, settings, vector

    def _protected(self, db, generation):
        return (
            db.scalar(select(Document.id).where(Document.active_generation_id == generation))
            is not None
            or db.scalar(
                select(AnswerCitation.id).where(AnswerCitation.generation_id == generation).limit(1)
            )
            is not None
            or db.scalar(
                select(ProcessingJob.id).where(
                    ProcessingJob.generation_id == generation,
                    ProcessingJob.status == "running",
                    ProcessingJob.lease_expires_at > func.clock_timestamp(),
                )
            )
            is not None
        )

    def sweep(self):
        # Allow bounded in-flight old inference/network work to stop, then reconcile again
        # on subsequent sweeps in case a stale worker wrote after an earlier deletion.
        grace = max(
            self.settings.orphan_grace_seconds,
            self.settings.job_lease_seconds
            + self.settings.embedding_timeout_seconds
            + self.settings.vector_timeout_seconds,
        )
        cutoff = datetime.now(UTC) - timedelta(seconds=grace)
        candidates = {}
        for point in self.vector.scroll():
            payload = point.get("payload") or {}
            try:
                generation = uuid.UUID(payload["generation_id"])
                born = float(payload["attempt_started_epoch"])
            except (KeyError, TypeError, ValueError):
                continue  # Never delete data without the worker's provenance.
            if born < cutoff.timestamp():
                candidates[generation] = True
        with self.sessions() as db:
            for model in (Chunk, SourceBlock):
                candidates.update(
                    {
                        generation: True
                        for generation in db.scalars(
                            select(model.generation_id)
                            .join(DocumentRevision, model.revision_id == DocumentRevision.id)
                            .where(
                                DocumentRevision.collection_name == self.vector.collection,
                                model.created_at < cutoff,
                            )
                            .distinct()
                        ).all()
                    }
                )
        cleaned = 0
        for generation in candidates:
            with self.sessions() as db:
                if self._protected(db, generation):
                    continue
            self.vector.delete_generation(generation)
            # No external I/O while these document locks are held.
            with self.sessions() as db:
                document_ids = db.scalars(
                    select(DocumentRevision.document_id)
                    .join(SourceBlock, SourceBlock.revision_id == DocumentRevision.id)
                    .where(SourceBlock.generation_id == generation)
                    .distinct()
                ).all()
                list(
                    db.scalars(
                        select(Document)
                        .where(Document.id.in_(document_ids))
                        .order_by(Document.id)
                        .with_for_update()
                    )
                )
                if self._protected(db, generation):
                    continue
                db.execute(delete(Chunk).where(Chunk.generation_id == generation))
                db.execute(delete(SourceBlock).where(SourceBlock.generation_id == generation))
                db.commit()
                cleaned += 1
        files = 0
        root = self.settings.storage_dir.resolve()
        for path in root.glob("*/*"):
            if (
                not path.is_file()
                or path.is_symlink()
                or path.parent.is_symlink()
                or not path.resolve().is_relative_to(root)
                or not re.fullmatch(
                    r"[0-9a-f]{32}/[0-9a-f]{32}\.(pdf|docx|txt|md)",
                    path.relative_to(root).as_posix(),
                )
                or path.stat().st_mtime > time.time() - grace
            ):
                continue
            with self.sessions() as db:
                referenced = db.scalar(
                    select(DocumentRevision.id)
                    .where(DocumentRevision.storage_key == path.relative_to(root).as_posix())
                    .limit(1)
                )
                if referenced is None:
                    path.unlink(missing_ok=True)
                    files += 1
        return {"generations": cleaned, "files": files}
