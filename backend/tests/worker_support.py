"""Real PostgreSQL/Qdrant reliability contracts. Embeddings here are labeled test fakes."""

import asyncio
import io
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import case, delete, select, update
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import UploadFile

from app.core.config import get_settings
from app.models import (
    Chunk,
    Document,
    DocumentRevision,
    ProcessingJob,
    SourceBlock,
    User,
    Workspace,
)
from app.services.embeddings import content_hash
from app.services.jobs import JobQueue
from app.services.parsing import PARSER_VERSION
from app.services.uploads import register_upload, store_stream
from app.services.vectors import QdrantIndex
from app.worker import IngestionWorker
from tests.test_parsing_chunking import CharacterCounter


class FakeEmbedder:
    """Deterministic unit vectors; never report these tests as AI quality measurements."""

    def encode(self, texts):
        return [[1.0] + [0.0] * 383 for _ in texts]


def fake_profile(settings):
    fingerprint = {"test_fake": True, "dimension": 384}
    return {
        "embedding_fingerprint": fingerprint,
        "embedding_hash": content_hash(fingerprint),
        "index_version": content_hash({"test_fake": True, "parser": PARSER_VERSION}),
        "parser_version": PARSER_VERSION,
        "chunking_config": {"test_fake": True},
        "collection_name": settings.qdrant_collection,
    }


@pytest.fixture
def worker_env(db_engine, tmp_path):
    settings = get_settings().model_copy(
        update={
            "storage_dir": tmp_path,
            "qdrant_collection": "s6_test_" + uuid.uuid4().hex[:12],
            "job_lease_seconds": 2,
            "job_heartbeat_seconds": 0.2,
            "embedding_timeout_seconds": 0.1,
            "orphan_grace_seconds": 1,
            "vector_timeout_seconds": 2,
        }
    )
    sessions = sessionmaker(db_engine, expire_on_commit=False)
    workspace_id, user_id = uuid.uuid4(), uuid.uuid4()
    with sessions() as db:
        db.add(Workspace(id=workspace_id, name="Isolated worker reliability tests"))
        db.flush()
        db.add(
            User(
                id=user_id,
                workspace_id=workspace_id,
                username="worker." + user_id.hex,
                email=user_id.hex + "@example.invalid",
                display_name="Worker test",
                password_hash="unused-service-fixture",
                role="knowledge_admin",
            )
        )
        db.commit()
    vector = QdrantIndex(settings.qdrant_url, settings.qdrant_collection, 2)
    profile = fake_profile(settings)
    vector.ensure_collection(profile["embedding_hash"])
    queue = JobQueue(sessions, settings)
    env = SimpleNamespace(
        settings=settings,
        sessions=sessions,
        vector=vector,
        queue=queue,
        profile=profile,
        user=SimpleNamespace(id=user_id, workspace_id=workspace_id),
        counter=CharacterCounter(),
        embedder=FakeEmbedder(),
    )

    def upload(body=b"A short sample policy.", extension="txt"):
        file = UploadFile(io.BytesIO(body))
        stored = asyncio.run(store_stream(file, tmp_path, workspace_id, extension, 20 * 1024**2))
        with sessions() as db:
            return register_upload(db, env.user, "source." + extension, extension, stored)

    env.upload = upload
    env.worker = lambda: IngestionWorker(queue, vector, env.embedder, env.counter, profile)
    try:
        yield env
    finally:
        assert settings.qdrant_collection.startswith("s6_test_")
        vector._request("DELETE", allow_missing=True)
        vector.close()
        with sessions() as db:
            ids = select(Document.id).where(Document.workspace_id == workspace_id)
            revisions = select(DocumentRevision.id).where(DocumentRevision.document_id.in_(ids))
            db.execute(
                update(Document)
                .where(Document.workspace_id == workspace_id)
                .values(
                    status=case((Document.status == "deleted", "deleted"), else_="failed"),
                    active_revision_id=None,
                    active_generation_id=None,
                )
            )
            db.execute(delete(ProcessingJob).where(ProcessingJob.document_id.in_(ids)))
            db.execute(delete(Chunk).where(Chunk.revision_id.in_(revisions)))
            db.execute(delete(SourceBlock).where(SourceBlock.revision_id.in_(revisions)))
            db.execute(delete(DocumentRevision).where(DocumentRevision.document_id.in_(ids)))
            db.execute(delete(Document).where(Document.workspace_id == workspace_id))
            db.execute(delete(User).where(User.id == user_id))
            db.execute(delete(Workspace).where(Workspace.id == workspace_id))
            db.commit()
