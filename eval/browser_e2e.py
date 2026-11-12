"""Loopback disposable browser E2E; production UI/API with scoped native budget."""

from __future__ import annotations

import argparse
import threading
import uuid
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import func, select

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import hash_password
from app.models import Document, DocumentRevision, ProcessingJob, User, Workspace
from app.services.chunking import E5TokenCounter
from app.services.cleanup import CleanupQueue, CleanupWorker
from app.services.embeddings import LocalEmbedder
from app.services.gemini import GeminiProvider
from app.services.jobs import JobQueue
from app.services.vectors import QdrantIndex
from app.worker import IngestionWorker
from eval.final_budget import RequestLedger, fingerprint
from eval.final_eval import read_json, run_replay, sha256, verify, write_json
from eval.run_capture_smoke import (
    cleanup,
    database,
    native_http_events,
    parser_packages,
    preflight,
    prepare_inputs,
)
from eval.runtime_capture import CaptureRuntime, SqlCanonicalSources

ROOT = Path(__file__).resolve().parents[1]
SCOPE = "browser-e2e-20261110"
PORT = 8012
CAPS = {"generateContent": 8, "countTokens": 28}
PASSWORD = "Disposable-browser-E2E-20261110!"
PLAN = (
    ("admin-answer", "Thời hạn nộp đề nghị hoàn ứng là bao lâu và cần giấy tờ gì?", False),
    ("admin-abstain", "Công ty quy định bao nhiêu ngày nghỉ phép năm cho mỗi nhân viên?", True),
    (
        "member-answer",
        "Tôi kết thúc công tác thì có bao nhiêu ngày nộp hoàn ứng, hồ sơ gồm gì?",
        False,
    ),
    ("member-abstain", "Mỗi năm nhân viên được nghỉ phép bao nhiêu ngày theo tài liệu?", True),
    ("admin-after-delete", "Sau khi nguồn bị xóa, hãy cho biết lại thời hạn hoàn ứng.", True),
    ("member-after-delete", "Nguồn vừa xóa còn cho biết tôi cần hồ sơ gì để hoàn ứng không?", True),
)


class RetryLedger:
    """Reserve the original global allowance first; failures never refund either file."""

    def __init__(self, parent, child):
        if (
            parent.grant["total"] != child.grant["total"]
            or parent.grant["batches"] != child.grant["batches"]
            or child.grant["scope_id"] != parent.grant["scope_id"] + "-retry-01"
        ):
            raise ValueError("Retry cannot expand the original grant")
        parent.bind_runtime(fingerprint({"retry_grant": child.grant}))
        self.parent, self.child = parent, child

    @property
    def grant(self):
        return self.child.grant

    def bind_runtime(self, digest):
        return self.child.bind_runtime(digest)

    def reserve(self, batch, action, query_id):
        self.parent.reserve(batch, action, query_id)
        return self.child.reserve(batch, action, query_id)

    def snapshot(self):
        return {**self.child.snapshot(), "global_allowance": self.parent.snapshot()}


def retry_parent(root):
    """Only reopen a cleaned, entirely unused browser scope; verify archived provenance."""
    output = root / ".cache" / SCOPE
    summary = read_json(output / "summary.json")
    if (
        summary.get("scope") != SCOPE
        or summary.get("cleanup_completed") is not True
        or any(summary.get(key) for key in ("api_events", "worker", "native_http_events"))
        or not (output / "finish").is_file()
    ):
        raise ValueError("Previous scope must be stopped, cleaned and unused")
    protocol = read_json(output / "protocol.json")
    verify(output / "frozen-root", protocol)
    grant = read_json(output / "grant.json")
    expected_batches = {
        identity: {"generateContent": 0, "countTokens": 0}
        if identity.endswith("after-delete")
        else {"generateContent": 2, "countTokens": 7}
        for identity, _, _ in PLAN
    }
    if grant != {
        "scope_id": SCOPE,
        "protocol_sha256": fingerprint(protocol),
        "total": CAPS,
        "batches": expected_batches,
    }:
        raise ValueError("Original grant differs from approved E2E scope")
    ledger = RequestLedger(output / "requests.sqlite", grant)
    snapshot = ledger.snapshot()
    with ledger._connect() as db:
        bound = db.execute("SELECT count(*) FROM runtime_binding").fetchone()[0]
    if bound or any(snapshot["total"].values()) or summary.get("ledger") != snapshot:
        raise ValueError("Previous scope has reservations or a runtime binding")
    hashes = read_json(output / "ui-bundle-sha256.json")
    actual = {
        path.relative_to(root / "frontend/dist").as_posix(): sha256(path)
        for path in (root / "frontend/dist").rglob("*")
        if path.is_file()
    }
    if actual != hashes:
        raise ValueError("UI bundle differs from approved archived build")
    return ledger


class Controller:
    """Bind after real browser upload/publication, before any LLM request."""

    def __init__(self, sessions, settings, profile, rows, mapping, protocol, ledger, users, app):
        self.sessions, self.settings, self.profile = sessions, settings, profile
        self.rows, self.mapping, self.protocol, self.ledger = rows, mapping, protocol, ledger
        self.users, self.app = users, app
        self.workspace_id = users["admin"].workspace_id
        self.lock, self.runtime = threading.RLock(), None

    def document(self):
        with self.sessions() as db:
            docs = db.scalars(
                select(Document).where(Document.workspace_id == self.workspace_id)
            ).all()
            if len(docs) != 1 or docs[0].sha256 != self.mapping["documents"]["policy"]["sha256"]:
                raise AppError(
                    503, "e2e_corpus_not_ready", "Upload the exact synthetic fixture first."
                )
            return docs[0]

    def observer_for(self, user, payload, settings):
        with self.lock:
            doc = self.document()
            after = any(
                row["question"] == payload.question and row["id"].endswith("after-delete")
                for row in self.rows
            )
            if after and doc.status not in {"deleting", "deleted"}:
                raise AppError(
                    409, "e2e_phase_not_ready", "Post-delete query requires disabled source."
                )
            if self.runtime is None:
                if doc.status != "ready":
                    raise AppError(503, "e2e_corpus_not_ready", "Wait for ingestion to finish.")
                sources = SqlCanonicalSources(
                    self.sessions, self.workspace_id, {"policy": doc.id}, self.mapping, self.profile
                )
                specs = [
                    {
                        "id": row["id"],
                        "question": row["question"],
                        "user_id": str(self.users[row["id"].split("-")[0]].id),
                        "workspace_id": str(self.workspace_id),
                        "document_ids": [],
                        "batch": row["id"],
                    }
                    for row in self.rows
                ]
                self.runtime = CaptureRuntime(
                    ROOT,
                    self.protocol,
                    "dev",
                    specs,
                    self.ledger,
                    sources,
                    self.settings,
                    GeminiProvider,
                    provider_kind="native_gemini",
                    allow_live=True,
                )
                # The app's factory/SQL/search hooks are installed before startup below.
                # Default CaptureRuntime.install restrictions remain unchanged elsewhere.
                self.runtime.app = self.app
            return self.runtime.observer_for(user, payload, settings)

    def allow(self, method, path):
        if method in {"GET", "HEAD", "OPTIONS"}:
            return True
        if method == "POST" and path in {
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/chat/sessions",
            "/api/v1/chat/query",
            "/api/v1/search",
        }:
            return True
        if method == "POST" and path == "/api/v1/documents":
            with self.sessions() as db:
                return (
                    db.scalar(
                        select(func.count())
                        .select_from(Document)
                        .where(Document.workspace_id == self.workspace_id)
                    )
                    == 0
                )
        if method == "DELETE":
            try:
                return path == "/api/v1/documents/" + str(self.document().id)
            except AppError:
                return False
        return False


def configure_app(controller, runtime, summary):
    from fastapi.responses import FileResponse

    from app.core.db import get_db
    from app.core.errors import error_response

    app = controller.app

    def scoped_db():
        with controller.sessions() as db:
            yield db

    app.dependency_overrides[get_db] = scoped_db
    app.state.rag_settings = controller.settings.model_copy(deep=True)
    app.state.search_runtime = runtime
    app.state.query_capture_factory = controller.observer_for
    app.state.provider_factory = CaptureRuntime.reject_uncaptured

    @app.middleware("http")
    async def restrict(request, call_next):
        if not controller.allow(request.method, request.url.path):
            return error_response(
                request, 403, "e2e_endpoint_not_approved", "Outside disposable E2E scope."
            )
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            summary["api_events"].append(
                {"method": request.method, "path": request.url.path, "status": response.status_code}
            )
        return response

    @app.get("/__e2e/status")
    def status():
        with controller.sessions() as db:
            docs = db.scalars(
                select(Document).where(Document.workspace_id == controller.workspace_id)
            ).all()
            documents = [{"id": str(d.id), "status": d.status} for d in docs]
            jobs = db.execute(
                select(ProcessingJob.kind, ProcessingJob.status)
                .join(Document, Document.id == ProcessingJob.document_id)
                .where(Document.workspace_id == controller.workspace_id)
            ).all()
        return {
            "scope": SCOPE,
            "documents": documents,
            "jobs": [list(j) for j in jobs],
            "ledger": controller.ledger.snapshot(),
            "worker": summary.get("worker", []),
            "api_events": summary["api_events"],
            "native_http_events": summary.get("native_http_events", []),
        }

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        build = (ROOT / "frontend/dist").resolve()
        requested = (build / path).resolve()
        if requested.is_relative_to(build) and requested.is_file():
            return FileResponse(requested)
        return FileResponse(build / "index.html")

    return app


def serve(settings, *, retry_unused=False):
    import uvicorn

    from app.core import config

    url, profile = preflight(settings)
    url = url.set(database=url.database.removesuffix("_smoke_test") + "_browser_test")
    from tests.database_safety import validate_test_database_url

    validate_test_database_url(url.render_as_string(hide_password=False), settings.database_url)
    parent = retry_parent(ROOT) if retry_unused else None
    output = ROOT / ".cache" / SCOPE
    if retry_unused:
        output = output / "retry-01"
    output.mkdir(parents=True, exist_ok=False)
    summary = {
        "scope": SCOPE,
        "request_caps": CAPS,
        "budget_usd": 0,
        "invoice_cost_verified_usd": None,
        "api_events": [],
        "worker": [],
        "cleanup_completed": False,
        "human_review": "pending",
        "attempt": "retry-01" if retry_unused else "initial",
    }
    counter = E5TokenCounter(settings.hf_home / "hub")
    rows, mapping, protocol, ledger = prepare_inputs(
        ROOT,
        output,
        settings,
        profile,
        counter,
        question_plan=PLAN,
        scope_id=SCOPE + "-retry-01" if retry_unused else SCOPE,
        caps=CAPS,
        synthetic_e2e=True,
    )
    if parent is not None:
        previous = output.parent
        if read_json(previous / "config.json") != read_json(output / "config.json") or (
            sha256(previous / "data/policy.txt") != sha256(output / "data/policy.txt")
            or sha256(previous / "data/questions.jsonl") != sha256(output / "data/questions.jsonl")
        ):
            raise ValueError("Retry changed approved config/corpus/questions")
        ledger = RetryLedger(parent, ledger)
    scope = fingerprint(ledger.grant)[:16]
    scoped = settings.model_copy(
        update={
            "qdrant_collection": "final_" + scope,
            "storage_dir": ROOT / "backend/.cache/final-capture" / scope,
        }
    )
    profile = {**profile, "collection_name": scoped.qdrant_collection}
    config.get_settings = lambda: scoped
    from app.main import create_app

    embedder = LocalEmbedder(profile, scoped)
    vector = QdrantIndex(scoped.qdrant_url, scoped.qdrant_collection, scoped.vector_timeout_seconds)
    stop = threading.Event()
    with database(url) as sessions:
        space = uuid.uuid4()
        users = {
            role: SimpleNamespace(id=uuid.uuid4(), workspace_id=space)
            for role in ("admin", "member")
        }
        try:
            with sessions() as db:
                db.add(Workspace(id=space, name="Disposable browser E2E"))
                db.flush()
                for role, user in users.items():
                    db.add(
                        User(
                            id=user.id,
                            workspace_id=space,
                            username="e2e." + role,
                            email=role + "@browser-e2e.invalid",
                            display_name="E2E " + role,
                            role="knowledge_admin" if role == "admin" else "member",
                            password_hash=hash_password(PASSWORD),
                        )
                    )
                db.commit()
            vector.ensure_collection(profile["embedding_hash"])
            app = create_app()
            controller = Controller(
                sessions, scoped, profile, rows, mapping, protocol, ledger, users, app
            )
            runtime = SimpleNamespace(
                profile=profile,
                vector=vector,
                embedder=embedder,
                counter=counter,
                lock=threading.Lock(),
                close=lambda: None,
            )
            configure_app(controller, runtime, summary)
            server = uvicorn.Server(
                uvicorn.Config(
                    app, host="127.0.0.1", port=PORT, access_log=False, log_level="warning"
                )
            )

            def worker():
                ingestion = IngestionWorker(
                    JobQueue(sessions, scoped), vector, embedder, counter, profile
                )
                cleaner = CleanupWorker(CleanupQueue(sessions, scoped), vector)
                while not stop.wait(0.3):
                    if (output / "finish").exists():
                        server.should_exit = True
                        break
                    try:
                        result = ingestion.run_once() or cleaner.run_once()
                        if result:
                            summary["worker"].append(result)
                    except Exception as exc:
                        summary["worker"].append({"error_type": type(exc).__name__})
                        break

            write_json(
                output / "cases.json",
                {
                    "url": f"http://127.0.0.1:{PORT}/",
                    "questions": rows,
                    "fixture": str(output / "data/policy.txt"),
                },
            )
            with parser_packages(ROOT), native_http_events(summary):
                thread = threading.Thread(target=worker, name="e2e-scoped-worker", daemon=True)
                thread.start()
                try:
                    server.run()
                finally:
                    stop.set()
                    thread.join(timeout=150)
                    if thread.is_alive():
                        raise RuntimeError("Worker did not stop; do not clean concurrent work")
            if controller.runtime is not None:
                controller.runtime.export(output / "capture")
                run_replay(
                    ROOT,
                    output / "protocol.json",
                    output / "capture/capture.json",
                    output / "evaluation",
                    "dev",
                )
        finally:
            stop.set()
            embedder.close()
            with sessions() as db:
                keys = list(
                    db.scalars(
                        select(DocumentRevision.storage_key)
                        .join(Document, Document.id == DocumentRevision.document_id)
                        .where(Document.workspace_id == space)
                    )
                )
            try:
                cleanup(
                    sessions,
                    vector,
                    scoped,
                    space,
                    users["admin"].id,
                    [key for key in keys if key],
                    extra_user_ids=[users["member"].id],
                )
                summary["cleanup_completed"] = True
            finally:
                vector.close()
                summary["ledger"] = ledger.snapshot()
                write_json(output / "summary.json", summary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--retry-unused", action="store_true")
    args = parser.parse_args(argv)
    settings = Settings(_env_file=ROOT / ".env")
    if not args.serve:
        preflight(settings)
        if args.retry_unused:
            retry_parent(ROOT)
        print("E2E preflight passed; zero model calls")
        return 0
    serve(settings, retry_unused=args.retry_unused)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
