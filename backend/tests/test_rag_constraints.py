"""PostgreSQL rejects inconsistent RAG identities even without API validation."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import (
    AnswerCitation,
    ChatMessage,
    ChatSession,
    Chunk,
    Document,
    DocumentRevision,
    ProcessingJob,
    QueryRun,
    SourceBlock,
    User,
    Workspace,
)
from app.models.enums import UserRole


@pytest.fixture
def graph(db_session):
    workspace = Workspace(name="Constraint tests")
    db_session.add(workspace)
    db_session.flush()
    user = User(
        workspace_id=workspace.id,
        username="schema.user",
        email="schema@example.invalid",
        display_name="Schema",
        password_hash="not-for-login",
        role=UserRole.MEMBER,
    )
    db_session.add(user)
    db_session.flush()
    doc = Document(
        workspace_id=workspace.id,
        created_by=user.id,
        filename="source.txt",
        mime="text/plain",
        size_bytes=10,
        sha256="a" * 64,
    )
    db_session.add(doc)
    db_session.flush()
    revision = DocumentRevision(document_id=doc.id, version=1, storage_key="internal/source")
    session = ChatSession(workspace_id=workspace.id, created_by=user.id)
    db_session.add_all([revision, session])
    db_session.flush()
    return workspace, user, doc, revision, session


def reject(db, obj, constraint):
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add(obj)
        db.flush()
    assert constraint in error.value.orig.diag.constraint_name


def document(graph, **kwargs):
    workspace, user, *_ = graph
    return Document(
        workspace_id=workspace.id,
        created_by=user.id,
        filename="other.txt",
        mime="text/plain",
        size_bytes=10,
        sha256="b" * 64,
        **kwargs,
    )


def chunk(graph, index=0, generation=None, point=None):
    return Chunk(
        revision_id=graph[3].id,
        generation_id=generation or uuid.uuid4(),
        chunk_index=index,
        text="source text",
        text_sha256="c" * 64,
        location_json={},
        source_spans_json=[],
        vector_point_id=point or uuid.uuid4(),
        token_count=3,
    )


def run(graph, **kwargs):
    return QueryRun(
        session_id=graph[4].id,
        client_request_id=uuid.uuid4(),
        input_hash="d" * 64,
        question="Question",
        **kwargs,
    )


@pytest.mark.parametrize(
    ("field", "value", "constraint"),
    [
        ("size_bytes", -1, "size_nonnegative"),
        ("sha256", "invalid", "hash_format"),
        ("filename", " ", "filename_nonempty"),
        ("status", "ready", "ready_active"),
        ("lifecycle_version", 0, "lifecycle_positive"),
        ("status", "deleted", "deleted_timestamp"),
    ],
)
def test_document_checks_are_in_database(db_session, graph, field, value, constraint):
    row = document(graph)
    setattr(row, field, value)
    reject(db_session, row, constraint)


def test_duplicate_hash_stays_reserved_while_deleting_then_released(db_session, graph):
    doc = graph[2]
    doc.status = "deleting"
    db_session.flush()
    other = document(graph)
    other.sha256 = doc.sha256
    reject(db_session, other, "uq_documents_workspace_hash_live")
    doc.status = "deleted"
    doc.deleted_at = datetime.now(UTC)
    db_session.flush()
    replacement = document(graph)
    replacement.sha256 = doc.sha256
    db_session.add(replacement)
    db_session.flush()


def test_owner_workspace_fk_cannot_cross_workspace(db_session, graph):
    workspace = Workspace(name="Other")
    db_session.add(workspace)
    db_session.flush()
    row = document(graph)
    row.workspace_id = workspace.id
    reject(db_session, row, "fk_documents_creator_scope")


def test_active_revision_must_belong_to_document(db_session, graph):
    other = document(graph)
    db_session.add(other)
    db_session.flush()
    with pytest.raises(IntegrityError) as error, db_session.begin_nested():
        db_session.execute(
            text(
                "UPDATE documents SET active_revision_id=:rev, "
                "active_generation_id=:generation WHERE id=:id"
            ),
            {"rev": graph[3].id, "generation": uuid.uuid4(), "id": other.id},
        )
    assert error.value.orig.diag.constraint_name == "fk_documents_active_revision"


def test_revision_version_is_unique(db_session, graph):
    reject(
        db_session,
        DocumentRevision(document_id=graph[2].id, version=1, storage_key="other"),
        "uq_document_revisions_document_id",
    )


@pytest.mark.parametrize(
    ("field", "value", "constraint"),
    [
        ("text", " ", "text_nonempty"),
        ("token_count", -1, "counts_nonnegative"),
        ("chunk_index", -1, "counts_nonnegative"),
        ("text_sha256", "invalid", "hash_format"),
    ],
)
def test_chunk_checks_are_in_database(db_session, graph, field, value, constraint):
    row = chunk(graph)
    setattr(row, field, value)
    reject(db_session, row, constraint)


def test_chunk_identity_and_point_id_are_unique(db_session, graph):
    generation, point = uuid.uuid4(), uuid.uuid4()
    db_session.add(chunk(graph, generation=generation, point=point))
    db_session.flush()
    reject(db_session, chunk(graph, generation=generation), "uq_chunks_revision_id")
    reject(db_session, chunk(graph, index=1, point=point), "uq_chunks_vector_point_id")


def test_source_block_index_unique_within_attempt(db_session, graph):
    generation = uuid.uuid4()

    def block():
        return SourceBlock(
            revision_id=graph[3].id,
            generation_id=generation,
            block_index=0,
            raw_text="text",
            normalized_text="text",
            location_json={},
        )

    db_session.add(block())
    db_session.flush()
    reject(db_session, block(), "uq_source_blocks_revision_id")


def job(graph, kind="ingest", **kwargs):
    doc = graph[2]
    return ProcessingJob(
        document_id=doc.id,
        revision_id=graph[3].id,
        entity_type="document",
        entity_id=doc.id,
        kind=kind,
        **kwargs,
    )


@pytest.mark.parametrize("kind", ["ingest", "cleanup"])
def test_one_active_job_per_document_and_kind(db_session, graph, kind):
    first = job(graph, kind)
    db_session.add(first)
    db_session.flush()
    reject(db_session, job(graph, kind), "uq_jobs_active_" + kind)
    first.status = "failed"
    db_session.flush()
    db_session.add(job(graph, kind))
    db_session.flush()


def test_rag_running_requires_lease_and_generation(db_session, graph):
    reject(db_session, job(graph, status="running"), "running_lease")
    reject(db_session, job(graph, status="processing"), "legacy_or_rag")
    row = job(
        graph,
        status="running",
        lease_token=uuid.uuid4(),
        generation_id=uuid.uuid4(),
        lease_expires_at=datetime.now(UTC),
    )
    db_session.add(row)
    db_session.flush()


def test_job_revision_cannot_reference_another_document(db_session, graph):
    other = document(graph)
    db_session.add(other)
    db_session.flush()
    row = job(graph)
    row.document_id = other.id
    row.entity_id = other.id
    reject(db_session, row, "fk_jobs_revision_document")


def test_query_idempotency_and_one_running_per_session(db_session, graph):
    first = run(graph)
    db_session.add(first)
    db_session.flush()
    reject(db_session, run(graph), "uq_query_runs_running_session")
    first.status = "completed"
    db_session.flush()
    repeated = run(graph, status="completed")
    repeated.client_request_id = first.client_request_id
    reject(db_session, repeated, "uq_query_runs_session_id")
    db_session.add(run(graph))
    db_session.flush()


def test_messages_and_citations_unique_and_chunk_tombstone(db_session, graph):
    query = run(graph, status="completed")
    db_session.add(query)
    db_session.flush()
    message = ChatMessage(
        session_id=graph[4].id, query_run_id=query.id, role="assistant", content="answer"
    )
    db_session.add(message)
    db_session.flush()
    reject(
        db_session,
        ChatMessage(session_id=graph[4].id, query_run_id=query.id, role="assistant"),
        "uq_chat_messages_query_run_id",
    )
    source = chunk(graph)
    db_session.add(source)
    db_session.flush()

    def cite():
        return AnswerCitation(
            message_id=message.id,
            chunk_id=source.id,
            document_id=graph[2].id,
            revision_id=graph[3].id,
            generation_id=source.generation_id,
            evidence_id="E1",
            location_snapshot={},
            excerpt_snapshot="source text",
        )

    citation = cite()
    db_session.add(citation)
    db_session.flush()
    reject(db_session, cite(), "uq_answer_citations_message_id")
    db_session.delete(source)
    db_session.flush()
    db_session.expire(citation)
    assert citation.chunk_id is None
    assert db_session.get(ChatMessage, message.id) is not None


def test_raw_unknown_enum_is_rejected(db_session, graph):
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(
            text("UPDATE users SET role='invented_role' WHERE id=:id"), {"id": graph[1].id}
        )
