"""Pinned dense retrieval: scoped SQL snapshot, active-gen filter, fresh SQL revalidation."""

from __future__ import annotations

import math
import threading
import time
import uuid

from sqlalchemy import select

from app.core.errors import AppError
from app.models import Chunk, Document, DocumentRevision, Folder
from app.services.chunking import E5TokenCounter
from app.services.embeddings import LocalEmbedder, content_hash, frozen_profile, validate_vectors
from app.services.vectors import QdrantIndex
from app.services.worker_errors import WorkerError


class RetrievalRuntime:
    def __init__(self, settings):
        self.profile = frozen_profile(settings)
        self.vector = QdrantIndex(
            settings.qdrant_url, settings.qdrant_collection, settings.vector_timeout_seconds
        )
        try:
            self.vector.check_collection(self.profile["embedding_hash"])
            self.counter = E5TokenCounter(settings.hf_home / "hub")
            self.embedder = LocalEmbedder(self.profile, settings)
        except Exception:
            self.vector.close()
            raise
        self.lock = threading.Lock()

    def close(self):
        self.embedder.close()
        self.vector.close()


def _snapshots(db, workspace_id, ids, folder_ids=()):
    if folder_ids:
        found = set(
            db.scalars(
                select(Folder.id).where(
                    Folder.workspace_id == workspace_id, Folder.id.in_(folder_ids)
                )
            )
        )
        if found != set(folder_ids):
            raise AppError(404, "not_found", "Không tìm thấy tài nguyên.")
    if ids:
        documents = db.execute(
            select(Document.id, Document.status).where(
                Document.workspace_id == workspace_id, Document.id.in_(ids)
            )
        ).all()
        # Resolve all IDs before considering status to avoid leaking a foreign resource.
        if {row.id for row in documents} != set(ids):
            raise AppError(404, "not_found", "Không tìm thấy tài nguyên.")
        if any(row.status in {"deleting", "deleted"} for row in documents):
            raise AppError(410, "source_unavailable", "Nguồn không còn khả dụng.")
        if any(row.status != "ready" for row in documents):
            raise AppError(409, "document_not_ready", "Tài liệu chưa sẵn sàng.")
    statement = (
        select(
            Document.id,
            Document.active_revision_id,
            Document.active_generation_id,
            Document.lifecycle_version,
            DocumentRevision.index_version,
            DocumentRevision.embedding_fingerprint,
            DocumentRevision.collection_name,
        )
        .join(DocumentRevision, DocumentRevision.id == Document.active_revision_id)
        .where(
            Document.workspace_id == workspace_id,
            Document.status == "ready",
            DocumentRevision.document_id == Document.id,
            DocumentRevision.status == "ready",
        )
    )
    if ids:
        statement = statement.where(Document.id.in_(ids))
    if folder_ids:
        statement = statement.where(Document.folder_id.in_(folder_ids))
    return [dict(row) for row in db.execute(statement).mappings()]


def search(db, user, payload, settings, runtime_factory, deadline=None):
    started = time.perf_counter()
    workspace_id = user.workspace_id
    if payload.mode != "dense":
        raise AppError(422, "unsupported_retrieval_mode", "P0 chỉ hỗ trợ dense retrieval.")
    snapshots = _snapshots(
        db, workspace_id, payload.filters.document_ids, payload.filters.folder_ids
    )
    # End the read/auth transaction before model/native/network work. The service owns
    # this boundary; callers must commit their own run setup before invoking retrieval.
    db.commit()
    top_k = payload.top_k or settings.retrieval_top_k
    trace = {
        "mode": "dense",
        "candidate_k": settings.retrieval_candidate_k,
        "requested_top_k": top_k,
        "candidate_count": 0,
        "sql_rejected_count": 0,
        "duplicate_count": 0,
        "below_threshold_count": 0,
        "eligible_document_count": 0,
        "score_threshold": settings.retrieval_score_threshold,
        "resolved_document_ids": sorted(str(row["id"]) for row in snapshots),
    }

    def response(hits, reason, embedding=0.0, retrieval=0.0, sql=0.0):
        return {
            "hits": hits,
            "reason_code": reason,
            "trace": trace,
            "timings_ms": {
                "embedding": round(embedding, 3),
                "retrieval": round(retrieval, 3),
                "sql_validation": round(sql, 3),
                "total": round((time.perf_counter() - started) * 1000, 3),
            },
        }

    if not snapshots:
        return response([], "no_ready_documents")
    try:
        runtime = runtime_factory()
        profile = runtime.profile
        allowed = {
            row["id"]: row
            for row in snapshots
            if (
                row["index_version"] == profile["index_version"]
                and row["collection_name"] == profile["collection_name"]
                and content_hash(row["embedding_fingerprint"]) == profile["embedding_hash"]
            )
        }
        if not allowed or (payload.filters.document_ids and len(allowed) != len(snapshots)):
            raise AppError(
                503, "retrieval_unavailable", "Index chưa tương thích cấu hình truy xuất."
            )
        trace.update(index_version=profile["index_version"], eligible_document_count=len(allowed))
        if runtime.counter.count_query(payload.query) > 512:
            raise AppError(422, "question_too_long", "Câu truy vấn vượt token budget E5.")
        if not runtime.lock.acquire(blocking=False):
            raise AppError(429, "retrieval_busy", "Bộ truy xuất đang bận; vui lòng thử lại.")
        try:
            runtime.vector.check_collection(
                profile["embedding_hash"],
                **({"deadline": deadline} if deadline is not None else {}),
            )
            before = time.perf_counter()
            vector = runtime.embedder.encode_query(
                payload.query, **({"deadline": deadline} if deadline is not None else {})
            )
            validate_vectors([vector], 1)
            embedding_ms = (time.perf_counter() - before) * 1000
            before = time.perf_counter()
            candidates = runtime.vector.query(
                vector,
                workspace_id,
                [row["active_generation_id"] for row in allowed.values()],
                profile["index_version"],
                settings.retrieval_candidate_k,
                **({"deadline": deadline} if deadline is not None else {}),
            )
            retrieval_ms = (time.perf_counter() - before) * 1000
        finally:
            runtime.lock.release()
    except WorkerError as exc:
        if deadline is not None and time.monotonic() >= deadline:
            raise AppError(504, "model_timeout", "Truy vấn vượt thời gian cho phép.") from None
        raise AppError(
            503, "retrieval_unavailable", "Bộ truy xuất tạm thời chưa sẵn sàng."
        ) from exc
    trace["candidate_count"] = len(candidates)
    before = time.perf_counter()
    point_scores, payloads = {}, {}
    for candidate in candidates:
        try:
            point_id = uuid.UUID(str(candidate["id"]))
            score = candidate["score"]
            if (
                isinstance(score, bool)
                or not isinstance(score, (float, int))
                or not math.isfinite(score)
            ):
                raise ValueError
            if not isinstance(candidate.get("payload"), dict):
                raise ValueError
        except (KeyError, TypeError, ValueError) as exc:
            raise AppError(503, "retrieval_unavailable", "Kết quả vector không hợp lệ.") from exc
        if point_id in point_scores:
            trace["duplicate_count"] += 1
            continue
        point_scores[point_id], payloads[point_id] = float(score), candidate["payload"]
    rows = db.execute(
        select(Chunk, Document, DocumentRevision)
        .join(DocumentRevision, Chunk.revision_id == DocumentRevision.id)
        .join(Document, DocumentRevision.document_id == Document.id)
        .where(
            Chunk.vector_point_id.in_(point_scores),
            Document.id.in_(allowed),
            Document.workspace_id == workspace_id,
            Document.status == "ready",
            Document.active_revision_id == Chunk.revision_id,
            Document.active_generation_id == Chunk.generation_id,
            DocumentRevision.status == "ready",
            DocumentRevision.collection_name == profile["collection_name"],
            DocumentRevision.index_version == profile["index_version"],
        )
    ).all()
    hits = []
    valid_points = set()
    for chunk, document, revision in rows:
        snapshot = allowed[document.id]
        if (
            document.lifecycle_version != snapshot["lifecycle_version"]
            or chunk.revision_id != snapshot["active_revision_id"]
            or chunk.generation_id != snapshot["active_generation_id"]
        ):
            continue
        expected = {
            "chunk_id": str(chunk.id),
            "document_id": str(document.id),
            "revision_id": str(revision.id),
            "generation_id": str(chunk.generation_id),
            "workspace_id": str(workspace_id),
            "index_version": profile["index_version"],
        }
        if any(
            payloads[chunk.vector_point_id].get(key) != value for key, value in expected.items()
        ):
            continue
        valid_points.add(chunk.vector_point_id)
        score = point_scores[chunk.vector_point_id]
        if (
            settings.retrieval_score_threshold is not None
            and score < settings.retrieval_score_threshold
        ):
            trace["below_threshold_count"] += 1
            continue
        hits.append(
            {
                "chunk_id": str(chunk.id),
                "document_id": str(document.id),
                "revision_id": str(revision.id),
                "generation_id": str(chunk.generation_id),
                "score": score,
                "score_type": "cosine_similarity",
                "excerpt": chunk.text,
                "source": {
                    "file_name": document.filename,
                    "location": chunk.location_json,
                    "content_url": f"/api/v1/documents/{document.id}/content",
                    "chunk_url": f"/api/v1/documents/{document.id}/chunks/{chunk.id}",
                },
            }
        )
    trace["sql_rejected_count"] = len(point_scores) - len(valid_points)
    hits.sort(key=lambda hit: (-hit["score"], hit["chunk_id"]))
    reason = (
        None
        if hits
        else "below_calibrated_threshold"
        if trace["below_threshold_count"]
        else "no_retrieval_hits"
    )
    return response(
        hits[:top_k], reason, embedding_ms, retrieval_ms, (time.perf_counter() - before) * 1000
    )
