"""Synchronous query runs with short SQL transactions and source-checked replay."""

import hashlib
import time
import uuid
from datetime import timedelta

from sqlalchemy import func, select, update
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.core.errors import AppError
from app.models import (
    AnswerCitation,
    ChatMessage,
    ChatSession,
    Chunk,
    Document,
    DocumentRevision,
    QueryRun,
)
from app.schemas.search import SearchRequest
from app.services.access import run_for_user, session_for_user
from app.services.answering import (
    PROMPT_VERSION,
    abstention,
    build_context,
    generate_answer,
    remaining,
    render_answer,
)
from app.services.embeddings import content_hash
from app.services.privacy import evidence_provenance
from app.services.retrieval import search


def input_hash(payload):
    return content_hash(
        {
            "session_id": str(payload.session_id),
            "question": payload.question,
            "mode": payload.retrieval_mode,
            "top_k": payload.top_k,
            "document_ids": sorted(str(key) for key in payload.filters.document_ids),
        }
    )


def expire_runs(db, session_id):
    db.execute(
        update(QueryRun)
        .where(
            QueryRun.session_id == session_id,
            QueryRun.status == "running",
            QueryRun.deadline_at <= func.clock_timestamp(),
        )
        .values(status="failed", error_code="model_timeout", finished_at=func.clock_timestamp())
    )


def source_state(db, user, evidence, lock=False, deadline=None):
    """Return fresh, trusted source snapshots; fail closed on any final-context drift."""
    if not evidence:
        return []
    ids = sorted({uuid.UUID(row["document_id"]) for row in evidence})
    statement = select(Document).where(Document.id.in_(ids)).order_by(Document.id)
    if lock:
        milliseconds = max(
            1, int(min(5, remaining(deadline) if deadline is not None else 5) * 1000)
        )
        db.execute(select(func.set_config("lock_timeout", str(milliseconds), True)))
        statement = statement.with_for_update()
    docs = {
        str(doc.id): doc for doc in db.scalars(statement.execution_options(populate_existing=True))
    }
    current = []
    for row in evidence:
        doc = docs.get(row["document_id"])
        chunk = db.get(Chunk, uuid.UUID(row["chunk_id"]), populate_existing=True)
        rev = db.get(DocumentRevision, uuid.UUID(row["revision_id"]), populate_existing=True)
        if (
            doc is None
            or doc.workspace_id != user.workspace_id
            or doc.status != "ready"
            or str(doc.active_revision_id) != row["revision_id"]
            or str(doc.active_generation_id) != row["generation_id"]
            or ("lifecycle_version" in row and doc.lifecycle_version != row["lifecycle_version"])
            or chunk is None
            or str(chunk.revision_id) != row["revision_id"]
            or str(chunk.generation_id) != row["generation_id"]
            or ("excerpt" in row and chunk.text != row["excerpt"])
            or (
                "text_sha256" in row
                and hashlib.sha256(chunk.text.encode()).hexdigest() != row["text_sha256"]
            )
            or rev is None
            or rev.document_id != doc.id
            or rev.status != "ready"
        ):
            raise AppError(409, "source_changed", "Nguồn đã thay đổi; vui lòng gửi truy vấn mới.")
        current.append(
            {
                **row,
                "lifecycle_version": doc.lifecycle_version,
                "document_version": rev.version,
                "source_spans": chunk.source_spans_json,
                "text_sha256": hashlib.sha256(chunk.text.encode()).hexdigest(),
                "source": {
                    "file_name": doc.filename,
                    "location": chunk.location_json,
                    "content_url": f"/api/v1/documents/{doc.id}/content",
                    "chunk_url": f"/api/v1/documents/{doc.id}/chunks/{chunk.id}",
                },
            }
        )
    return current


class SourceCheckedProvider:
    """Token counting sends text remotely too; recheck before every provider operation."""

    def __init__(self, db, user, provider, evidence):
        self.db, self.user, self.provider, self.evidence = db, user, provider, evidence

    def _check(self, deadline):
        remaining(deadline)
        source_state(self.db, self.user, self.evidence)
        self.db.commit()  # Never hold the read transaction across provider I/O.

    def count_tokens(self, payload, deadline):
        self._check(deadline)
        return self.provider.count_tokens(payload, deadline)

    def generate(self, payload, deadline):
        self._check(deadline)
        return self.provider.generate(payload, deadline)


def run_data(db, user, run):
    result = {
        "id": str(run.id),
        "run_id": str(run.id),
        "session_id": str(run.session_id),
        "status": run.status,
        "error_code": run.error_code,
    }
    if run.status != "completed":
        return result
    message = db.scalar(
        select(ChatMessage).where(
            ChatMessage.query_run_id == run.id, ChatMessage.role == "assistant"
        )
    )
    if message is None:
        raise AppError(503, "database_unavailable", "Kết quả truy vấn chưa khả dụng.")
    try:
        if message.source_unavailable:
            raise AppError(409, "source_changed", "Nguồn không khả dụng.")
        source_state(db, user, run.retrieval_trace_json.get("evidence_map", []))
        citations = db.scalars(
            select(AnswerCitation).where(AnswerCitation.message_id == message.id)
        ).all()
        if any(c.source_status != "available" or c.chunk_id is None for c in citations):
            raise AppError(409, "source_changed", "Nguồn không khả dụng.")
    except AppError:
        return result | {
            "message_id": str(message.id),
            "source_unavailable": True,
            "answer": "",
            "claims": [],
            "citations": [],
            "limitations": [],
            "missing_information": [],
            "conflict_detected": False,
            "reason_code": "source_unavailable",
        }
    return result | message.structured_answer_json | {"source_unavailable": False}


def read_run(db, user, run_id):
    row = run_for_user(db, run_id, user)
    expire_runs(db, row.session_id)
    db.commit()
    row = db.get(QueryRun, row.id, populate_existing=True)
    return run_data(db, user, row)


def start_run(db, user, payload, settings):
    session_for_user(db, payload.session_id, user)
    try:
        db.scalar(
            select(ChatSession)
            .where(ChatSession.id == payload.session_id)
            .with_for_update(nowait=True)
        )
    except OperationalError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) == "55P03":
            raise AppError(409, "session_busy", "Session đang xử lý truy vấn.") from None
        raise
    expire_runs(db, payload.session_id)
    previous = db.scalar(
        select(QueryRun).where(
            QueryRun.session_id == payload.session_id,
            QueryRun.client_request_id == payload.client_request_id,
        )
    )
    if previous:
        db.commit()
        if previous.input_hash != input_hash(payload):
            raise AppError(409, "idempotency_conflict", "Client request ID đã dùng với input khác.")
        if previous.status == "running":
            raise AppError(
                409, "query_in_progress", "Truy vấn đang chạy.", {"run_id": str(previous.id)}
            )
        if previous.status == "failed":
            code = previous.error_code or "internal_error"
            status = previous.config_json.get(
                "failure_http_status", 504 if code == "model_timeout" else 503
            )
            raise AppError(
                status,
                code,
                "Truy vấn trước đã thất bại; dùng client request ID mới để thử lại.",
                {"run_id": str(previous.id)},
            )
        return previous, run_data(db, user, previous)
    active = db.scalar(
        select(QueryRun.id).where(
            QueryRun.session_id == payload.session_id, QueryRun.status == "running"
        )
    )
    if active:
        db.commit()
        raise AppError(409, "session_busy", "Session đang xử lý truy vấn.", {"run_id": str(active)})
    now = db.scalar(select(func.clock_timestamp()))
    row = QueryRun(
        session_id=payload.session_id,
        client_request_id=payload.client_request_id,
        input_hash=input_hash(payload),
        question=payload.question,
        started_at=now,
        deadline_at=now + timedelta(seconds=settings.query_timeout_seconds),
        config_json={
            "prompt_version": PROMPT_VERSION,
            "model": settings.llm_model,
            "evidence_budget_tokens": settings.llm_evidence_budget_tokens,
            "max_output_tokens": settings.llm_max_output_tokens,
            "context_window_tokens": settings.llm_context_window_tokens,
            "safety_margin_tokens": settings.llm_safety_margin_tokens,
            "thinking_level": "MINIMAL",
            "max_generation_calls": 2,
            "query_timeout_seconds": settings.query_timeout_seconds,
            "call_timeout_seconds": settings.llm_call_timeout_seconds,
            "retrieval_mode": payload.retrieval_mode,
            "top_k": payload.top_k or settings.retrieval_top_k,
            "candidate_k": settings.retrieval_candidate_k,
            "score_threshold": settings.retrieval_score_threshold,
            "filters": sorted(str(key) for key in payload.filters.document_ids),
        },
    )
    db.add(row)
    db.flush()
    db.add(
        ChatMessage(
            session_id=row.session_id, query_run_id=row.id, role="user", content=payload.question
        )
    )
    db.commit()
    return row, None


def fail_run(db, run_id, error):
    db.rollback()
    row = db.scalar(select(QueryRun).where(QueryRun.id == run_id).with_for_update(nowait=True))
    if row is not None and row.status == "running":
        row.status, row.error_code = "failed", error.code
        row.finished_at = db.scalar(select(func.clock_timestamp()))
        row.config_json = row.config_json | {"failure_http_status": error.status_code}
        db.commit()


def publish(db, user, run_id, evidence, answer, trace, reason, timings, deadline):
    remaining(deadline)
    # Same global order as future delete: documents before session/run locks.
    evidence = source_state(db, user, evidence, lock=True, deadline=deadline)
    run = db.get(QueryRun, run_id, populate_existing=True)
    db.scalar(
        select(ChatSession.id).where(ChatSession.id == run.session_id).with_for_update(nowait=True)
    )
    run = db.scalar(
        select(QueryRun)
        .where(QueryRun.id == run_id)
        .with_for_update(nowait=True)
        .execution_options(populate_existing=True)
    )
    now = db.scalar(select(func.clock_timestamp()))
    remaining(deadline)
    if run.status != "running" or now >= run.deadline_at:
        raise AppError(504, "model_timeout", "Truy vấn đã hết hạn.")
    cited = {key for claim in answer.claims for key in claim.evidence_ids}
    citations = [
        {
            "evidence_id": row["evidence_id"],
            "chunk_id": row["chunk_id"],
            "document_id": row["document_id"],
            "revision_id": row["revision_id"],
            "generation_id": row["generation_id"],
            "document_version": row["document_version"],
            "file_name": row["source"]["file_name"],
            "location": row["source"]["location"],
            "excerpt": row["excerpt"],
            "content_url": row["source"]["content_url"],
            "chunk_url": row["source"]["chunk_url"],
        }
        for row in evidence
        if row["evidence_id"] in cited
    ]
    data = answer.model_dump()
    if answer.answer_status == "insufficient_evidence":
        # Free-form model explanations are not published on abstention.
        data.update(limitations=[], missing_information=[])
    message_id = uuid.uuid4()
    data.update(
        run_id=str(run_id),
        message_id=str(message_id),
        answer=render_answer(answer),
        citations=citations,
        reason_code=reason,
        timings_ms=timings,
    )
    db.add(
        ChatMessage(
            id=message_id,
            session_id=run.session_id,
            query_run_id=run_id,
            role="assistant",
            content=data["answer"],
            structured_answer_json=data,
            answer_status=answer.answer_status,
        )
    )
    db.flush()
    for row in citations:
        db.add(
            AnswerCitation(
                message_id=message_id,
                chunk_id=uuid.UUID(row["chunk_id"]),
                document_id=uuid.UUID(row["document_id"]),
                revision_id=uuid.UUID(row["revision_id"]),
                generation_id=uuid.UUID(row["generation_id"]),
                evidence_id=row["evidence_id"],
                location_snapshot=row["location"],
                excerpt_snapshot=row["excerpt"],
            )
        )
    run.status, run.finished_at = "completed", now
    run.retrieval_trace_json = trace | {
        "evidence_map": evidence_provenance(evidence),
        "cited_ids": [row["chunk_id"] for row in citations],
    }
    db.commit()
    return run_data(db, user, run)


def query(db, user, payload, settings, runtime_factory, provider_factory, capacity):
    if payload.retrieval_mode != "dense":
        raise AppError(422, "unsupported_retrieval_mode", "P0 chỉ hỗ trợ dense retrieval.")
    # Pin a settings snapshot rather than reading mutable global config between calls.
    settings = settings.model_copy(deep=True)
    started = time.monotonic()
    run, replay = start_run(db, user, payload, settings)
    if replay is not None:
        return replay
    deadline = started + settings.query_timeout_seconds
    try:
        result = search(
            db,
            user,
            SearchRequest(
                query=payload.question,
                mode=payload.retrieval_mode,
                top_k=payload.top_k,
                filters=payload.filters,
            ),
            settings,
            runtime_factory,
            deadline=deadline,
        )
        remaining(deadline)
        hits = source_state(db, user, result["hits"])
        trace = result["trace"] | {"retrieved_ids": [row["chunk_id"] for row in hits]}
        db.commit()
        evidence, attempts, answer = [], [], abstention()
        reason = result["reason_code"]
        before_generation = time.monotonic()
        if hits:
            if not capacity.acquire(blocking=False):
                raise AppError(429, "model_busy", "Model đang bận; vui lòng gửi lại với ID mới.")
            try:
                provider = SourceCheckedProvider(db, user, provider_factory(settings), hits)
                evidence, context_trace = build_context(
                    payload.question, hits, settings, provider, deadline
                )
                trace |= context_trace
                provider.evidence = evidence
                # Persist exactly the map sent, without holding a SQL transaction during inference.
                # Lock/recheck before registration so delete cannot miss a new evidence map.
                evidence = source_state(db, user, evidence, lock=True, deadline=deadline)
                current_run = db.scalar(
                    select(QueryRun)
                    .where(QueryRun.id == run.id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
                if current_run.status != "running":
                    raise AppError(
                        409 if current_run.error_code == "source_changed" else 504,
                        current_run.error_code or "model_timeout",
                        "Truy vấn không còn khả dụng.",
                    )
                recorded = db.execute(
                    update(QueryRun)
                    .where(QueryRun.id == run.id, QueryRun.status == "running")
                    .values(
                        retrieval_trace_json=trace | {"evidence_map": evidence_provenance(evidence)}
                    )
                )
                db.commit()
                if recorded.rowcount != 1:
                    raise AppError(504, "model_timeout", "Truy vấn đã hết hạn.")
                if evidence:
                    answer, attempts = generate_answer(
                        payload.question, evidence, settings, provider, deadline
                    )
                    reason = (
                        "insufficient_support"
                        if answer.answer_status == "insufficient_evidence"
                        else None
                    )
                else:
                    reason = "context_budget_excluded"
            finally:
                capacity.release()
        trace |= {
            "generation_attempts": attempts,
            "final_context_ids": [row["chunk_id"] for row in evidence],
        }
        timings = {
            "retrieval": result["timings_ms"]["total"],
            "generation": round((time.monotonic() - before_generation) * 1000, 3),
            "total": round((time.monotonic() - started) * 1000, 3),
        }
        return publish(db, user, run.id, evidence, answer, trace, reason, timings, deadline)
    except AppError as exc:
        fail_run(db, run.id, exc)
        exc.details = {"run_id": str(run.id)}
        raise
    except SQLAlchemyError:
        try:
            fail_run(db, run.id, AppError(503, "database_unavailable", "Database chưa khả dụng."))
        except SQLAlchemyError:
            db.rollback()  # Recovery/replay checks deadline if DB remains unavailable.
        raise
    except Exception:
        fail_run(db, run.id, AppError(500, "internal_error", "Lỗi hệ thống."))
        raise
