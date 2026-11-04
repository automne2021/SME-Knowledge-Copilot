"""Minimal evidence provenance and irreversible redaction of affected chat copies."""

from sqlalchemy import func, or_, select

from app.models import AnswerCitation, ChatMessage, ChatSession, QueryRun

EVIDENCE_FIELDS = (
    "evidence_id",
    "chunk_id",
    "document_id",
    "revision_id",
    "generation_id",
    "lifecycle_version",
    "document_version",
    "text_sha256",
    "source_spans",
)


def evidence_provenance(evidence):
    result = []
    for row in evidence:
        item = {key: row[key] for key in EVIDENCE_FIELDS if key in row and key != "source_spans"}
        if "source_spans" in row:
            item["source_spans"] = [
                {
                    key: span[key]
                    for key in ("block_id", "char_start", "char_end", "role")
                    if key in span
                }
                for span in row["source_spans"]
            ]
        result.append(item)
    return result


def redact_document(db, document):
    cited_runs = (
        select(ChatMessage.query_run_id)
        .join(AnswerCitation, AnswerCitation.message_id == ChatMessage.id)
        .where(AnswerCitation.document_id == document.id)
    )
    runs = db.scalars(
        select(QueryRun)
        .join(ChatSession, ChatSession.id == QueryRun.session_id)
        .where(
            ChatSession.workspace_id == document.workspace_id,
            or_(
                QueryRun.id.in_(cited_runs),
                QueryRun.retrieval_trace_json.contains(
                    {"evidence_map": [{"document_id": str(document.id)}]}
                ),
            ),
        )
        .order_by(QueryRun.id)
        .with_for_update(of=QueryRun)
    ).all()
    for run in runs:
        # Drop all debug/free text in this run, including copies from uncited context.
        run.retrieval_trace_json = {
            "evidence_map": evidence_provenance(run.retrieval_trace_json.get("evidence_map", [])),
            "source_unavailable": True,
        }
        if run.status == "running":
            run.status, run.error_code = "failed", "source_changed"
            run.finished_at = db.scalar(select(func.clock_timestamp()))
            run.config_json = run.config_json | {"failure_http_status": 409}
        messages = db.scalars(
            select(ChatMessage).where(
                ChatMessage.query_run_id == run.id, ChatMessage.role == "assistant"
            )
        ).all()
        for message in messages:
            message.content, message.structured_answer_json = "", None
            message.source_unavailable = True
            for citation in db.scalars(
                select(AnswerCitation).where(AnswerCitation.message_id == message.id)
            ):
                citation.excerpt_snapshot, citation.location_snapshot = None, {}
                citation.source_status = "unavailable"
