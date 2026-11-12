"""Opt-in, scoped API capture using production chat hooks and a persistent budget.

No service starts, settings load, DB connections or provider construction on import.
The caller supplies an isolated app, verified SQL sources and an approved grant.
"""

from __future__ import annotations

import copy
import json
import threading
import time
import uuid
from pathlib import Path

from app.core.errors import AppError
from app.schemas.answer import StructuredAnswer
from eval.final_budget import BudgetExceeded, GuardedProvider, LedgerUnavailable, fingerprint
from eval.final_eval import evaluate_capture, inside, load_questions, read_json, verify, write_json

SETTINGS_FIELDS = (
    "embedding_model",
    "embedding_revision",
    "embedding_dimension",
    "chunk_size_tokens",
    "chunk_overlap_tokens",
    "retrieval_candidate_k",
    "retrieval_top_k",
    "retrieval_score_threshold",
    "llm_model",
    "llm_base_url",
    "llm_evidence_budget_tokens",
    "llm_max_output_tokens",
    "llm_safety_margin_tokens",
    "llm_context_window_tokens",
    "query_timeout_seconds",
    "llm_call_timeout_seconds",
    "qdrant_url",
    "qdrant_collection",
    "storage_dir",
)


def settings_hash(settings):
    # Never serialize the settings object: it includes credentials and private paths.
    return fingerprint(
        {
            key: str(getattr(settings, key))
            if isinstance(getattr(settings, key), Path)
            else getattr(settings, key)
            for key in SETTINGS_FIELDS
        }
    )


class SqlCanonicalSources:
    """Fresh SQL scope/lifecycle/canonical mapping validation on every capture event."""

    def __init__(self, sessions, workspace_id, uploaded, mapping, profile):
        self.sessions, self.workspace_id = sessions, workspace_id
        self.uploaded, self.mapping, self.profile = uploaded, mapping, profile

    def references(self, hits):
        from sqlalchemy import select

        from app.models import Chunk, Document
        from eval.retrieval_gold import load_active_mapping

        reverse = {str(value): key for key, value in self.uploaded.items()}
        needed = {reverse.get(str(hit["document_id"])) for hit in hits}
        if None in needed:
            raise ValueError("Capture source is outside the fixed corpus")
        if not needed:
            return []
        uploaded = {key: self.uploaded[key] for key in needed}
        mapping = {
            **self.mapping,
            "documents": {key: self.mapping["documents"][key] for key in needed},
        }
        with self.sessions() as db:
            loaded = load_active_mapping(db, self.workspace_id, uploaded, mapping, self.profile)
            by_id = {}
            for reference, document_id in uploaded.items():
                document = db.get(Document, document_id)
                chunks = db.scalars(
                    select(Chunk)
                    .where(
                        Chunk.revision_id == document.active_revision_id,
                        Chunk.generation_id == document.active_generation_id,
                    )
                    .order_by(Chunk.chunk_index)
                ).all()
                for index, chunk in enumerate(chunks):
                    by_id[str(chunk.id)] = (
                        {
                            "document_id": reference,
                            "chunk_index": index,
                            "text_sha256": chunk.text_sha256,
                        },
                        str(document_id),
                        str(chunk.revision_id),
                        str(chunk.generation_id),
                    )
            result = []
            for hit in hits:
                identity = by_id.get(str(hit["chunk_id"]))
                if (
                    identity is None
                    or (str(hit["document_id"]), str(hit["revision_id"]), str(hit["generation_id"]))
                    != identity[1:]
                    or hit["excerpt"] != loaded["chunk_text"][str(hit["chunk_id"])]
                ):
                    raise ValueError("Capture hit differs from active canonical SQL source")
                result.append(identity[0])
            return result


class CaptureRuntime:
    """Install only on a new, separate app; regular APIs remain unaffected.

    Specs pin question text, user/workspace, top-k, filters and batch. One new
    client_request_id is admitted per spec; identical idempotent replay is allowed.
    Every provider entry outside an admitted observer fails closed.
    """

    def __init__(
        self,
        root,
        protocol,
        split,
        specs,
        ledger,
        sources,
        settings,
        transport_factory,
        *,
        provider_kind="fake",
        allow_live=False,
        allow_heldout=False,
    ):
        self.root, self.protocol, self.split = Path(root), copy.deepcopy(protocol), split
        self.ledger, self.sources = ledger, sources
        self.transport_factory, self.provider_kind = transport_factory, provider_kind
        self._settings_snapshot = settings.model_copy(deep=True)
        self.allow_heldout = allow_heldout
        self.settings_sha256 = settings_hash(settings)
        if ledger.grant["protocol_sha256"] != fingerprint(protocol):
            raise ValueError("Ledger is not bound to this frozen protocol")
        if provider_kind not in {"fake", "native_gemini"}:
            raise ValueError("Explicit provider kind required")
        if provider_kind == "native_gemini":
            from app.services.gemini import GeminiProvider

            if not allow_live or transport_factory is not GeminiProvider:
                raise ValueError("Native calls require explicit authorization and native provider")
            # Constructor validates manual flags, not billing/quota with the provider.
            GeminiProvider(settings)
        self.origin = (
            "captured_api"
            if isinstance(sources, SqlCanonicalSources) and provider_kind == "native_gemini"
            else "offline_fixture"
        )
        if isinstance(sources, SqlCanonicalSources):
            self._validate_sql_scope(settings)
        questions = {q["id"]: q for q in load_questions(root, protocol, split, allow_heldout)}
        config = read_json(inside(root, protocol["config"]))
        expected = {
            "model": settings.embedding_model,
            "revision": settings.embedding_revision,
            "dimension": settings.embedding_dimension,
            "candidate_k": settings.retrieval_candidate_k,
            "chunk_size_tokens": settings.chunk_size_tokens,
            "chunk_overlap_tokens": settings.chunk_overlap_tokens,
            "score_threshold": settings.retrieval_score_threshold,
        }
        if any(key in config and config[key] != value for key, value in expected.items()):
            raise ValueError("Runtime differs from the frozen retrieval config")
        if isinstance(sources, SqlCanonicalSources) and config.get("expected_index_version") != (
            sources.profile.get("index_version")
        ):
            raise ValueError("SQL index profile differs from frozen retrieval config")
        self.specs, keys = {}, set()
        for spec in copy.deepcopy(specs):
            if set(spec) != {"id", "question", "user_id", "workspace_id", "document_ids", "batch"}:
                raise ValueError("Invalid query plan fields")
            if (
                spec["id"] in self.specs
                or spec["id"] not in questions
                or spec["question"] != (questions[spec["id"]]["question"])
                or spec["batch"] not in ledger.grant["batches"]
            ):
                raise ValueError("Query plan differs from frozen questions/batches")
            for field in ("user_id", "workspace_id"):
                spec[field] = str(uuid.UUID(spec[field]))
            spec["document_ids"] = sorted(str(uuid.UUID(item)) for item in spec["document_ids"])
            if len(set(spec["document_ids"])) != len(spec["document_ids"]):
                raise ValueError("Duplicate document filter")
            if isinstance(sources, SqlCanonicalSources) and spec["workspace_id"] != str(
                sources.workspace_id
            ):
                raise ValueError("Capture workspace differs from SQL source scope")
            key = (spec["user_id"], spec["workspace_id"], spec["question"].strip())
            if key in keys:
                raise ValueError("Ambiguous question/user binding")
            keys.add(key)
            self.specs[spec["id"]] = spec
        if not self.specs or config["production_top_k"] != settings.retrieval_top_k:
            raise ValueError("Missing queries or top-k config drift")
        self.top_k = config["production_top_k"]
        self.plan_sha256 = self._plan_hash()
        ledger.bind_runtime(self.plan_sha256)
        self.lock, self.attempts, self.app = threading.RLock(), {}, None

    def _plan_hash(self):
        source_binding = None
        if isinstance(self.sources, SqlCanonicalSources):
            source_binding = {
                "workspace_id": str(self.sources.workspace_id),
                "uploaded": {key: str(value) for key, value in self.sources.uploaded.items()},
                "mapping": fingerprint(self.sources.mapping),
                "index_version": self.sources.profile.get("index_version"),
                "collection_name": self.sources.profile.get("collection_name"),
            }
        return fingerprint(
            {
                "protocol": fingerprint(self.protocol),
                "split": self.split,
                "specs": self.specs,
                "settings_sha256": self.settings_sha256,
                "provider_kind": self.provider_kind,
                "source_adapter": "sql_canonical"
                if isinstance(self.sources, SqlCanonicalSources)
                else "fixture",
                "origin": self.origin,
                "sources": source_binding,
            }
        )

    def _validate_sql_scope(self, settings):
        from tests.database_safety import validate_test_database_url

        sources = self.sources
        engine = getattr(sources.sessions, "kw", {}).get("bind")
        if engine is None or not hasattr(engine, "url"):
            raise ValueError("Scoped SQL sessionmaker must expose its actual engine target")
        validate_test_database_url(
            engine.url.render_as_string(hide_password=False), settings.database_url
        )
        scope = fingerprint(self.ledger.grant)[:16]
        expected_collection = "final_" + scope
        expected_storage = self.root.resolve() / "backend/.cache/final-capture" / scope
        if (
            settings.qdrant_collection != expected_collection
            or sources.profile.get("collection_name") != expected_collection
            or settings.storage_dir.resolve() != expected_storage
        ):
            raise ValueError("SQL capture requires its own collection and storage directory")
        if fingerprint(sources.mapping) != fingerprint(
            read_json(inside(self.root, self.protocol["mapping"]))
        ):
            raise ValueError("SQL source mapping differs from frozen protocol")

    def install(self, app, search_runtime=None):
        if (
            self.app is not None
            or app.middleware_stack is not None
            or hasattr(app.state, "query_capture_factory")
        ):
            raise ValueError("Install capture only once on a fresh isolated app")
        if isinstance(self.sources, SqlCanonicalSources):
            from app.core.db import get_db

            if search_runtime is None or search_runtime.profile != self.sources.profile:
                raise ValueError("Explicit matching search runtime required for SQL capture")

            def scoped_db():
                with self.sources.sessions() as db:
                    yield db

            app.dependency_overrides[get_db] = scoped_db
            app.state.search_runtime = search_runtime
        self.app = app
        app.state.rag_settings = self._settings_snapshot.model_copy(deep=True)
        app.state.query_capture_factory = self.observer_for
        app.state.provider_factory = self.reject_uncaptured

        @app.middleware("http")
        async def restrict_scope_endpoints(request, call_next):
            from app.core.errors import error_response

            allowed_posts = {
                "/api/v1/auth/login",
                "/api/v1/auth/logout",
                "/api/v1/search",
                "/api/v1/chat/sessions",
                "/api/v1/chat/query",
            }
            if request.method not in {"GET", "HEAD", "OPTIONS"} and not (
                request.method == "POST" and request.url.path in allowed_posts
            ):
                return error_response(
                    request,
                    403,
                    "eval_endpoint_not_approved",
                    "This operation is outside the capture scope.",
                )
            return await call_next(request)

        return app

    @staticmethod
    def reject_uncaptured(settings):
        raise AppError(503, "eval_scope_required", "Model calls require the active eval scope.")

    def observer_for(self, user, payload, settings):
        verify(self.root, self.protocol)
        if self._plan_hash() != self.plan_sha256:
            raise AppError(503, "eval_plan_drift", "Runtime plan changed after binding.")
        if settings_hash(settings) != self.settings_sha256:
            raise AppError(503, "eval_config_drift", "Settings differ from the pinned runtime.")
        candidates = [
            spec
            for spec in self.specs.values()
            if (spec["user_id"], spec["workspace_id"], spec["question"].strip())
            == (str(user.id), str(user.workspace_id), payload.question)
        ]
        if len(candidates) != 1:
            raise AppError(403, "eval_query_not_approved", "Query is outside the fixed eval plan.")
        spec = candidates[0]
        if (
            payload.retrieval_mode != "dense"
            or (payload.top_k or self.top_k) != self.top_k
            or sorted(str(item) for item in payload.filters.document_ids) != spec["document_ids"]
        ):
            raise AppError(403, "eval_query_not_approved", "Retrieval scope differs from the plan.")
        request_hash = fingerprint(payload.model_dump(mode="json"))
        with self.lock:
            existing = self.attempts.get(spec["id"])
            if existing is not None:
                if existing.request_hash != request_hash:
                    raise AppError(409, "eval_attempt_already_used", "Query attempt already used.")
                if existing.row is None:
                    raise AppError(409, "eval_request_in_progress", "Query is still running.")
                return ReplayObserver()
            observer = QueryObserver(self, spec, request_hash, str(payload.client_request_id))
            self.attempts[spec["id"]] = observer
            return observer

    def export(self, output):
        if self._plan_hash() != self.plan_sha256:
            raise ValueError("Runtime plan changed after binding")
        with self.lock:
            if any(attempt.row is None for attempt in self.attempts.values()):
                raise ValueError("Cannot export while an admitted request is still running")
            capture = {
                "schema": 1,
                "protocol_sha256": fingerprint(self.protocol),
                "origin": self.origin,
                "split": self.split,
                "rows": [copy.deepcopy(attempt.row) for attempt in self.attempts.values()],
            }
            events = {key: copy.deepcopy(attempt.calls) for key, attempt in self.attempts.items()}
        evaluate_capture(self.root, self.protocol, capture, self.split, self.allow_heldout)
        ledger_snapshot = self.ledger.snapshot()
        output = Path(output)
        if output.resolve().is_relative_to(inside(self.root, self.protocol["dataset"])):
            raise ValueError("Capture output overlaps reviewed dataset")
        output.mkdir(parents=True, exist_ok=False)
        write_json(output / "capture.json", capture)
        write_json(
            output / "execution.json",
            {
                "schema": 1,
                "kind": "scoped_api_capture",
                "provider_kind": self.provider_kind,
                "plan_sha256": self.plan_sha256,
                "protocol_sha256": fingerprint(self.protocol),
                "origin": self.origin,
                "ledger": ledger_snapshot,
                "calls": events,
                "chat_retrieval_top_k": self.top_k,
                "heldout_acceptance": "pending",
                "capture_provenance_independently_verified": False,
                "auth_override_present": bool(
                    self.app
                    and any(
                        getattr(dependency, "__name__", "") == "get_current_user"
                        for dependency in self.app.dependency_overrides
                    )
                ),
            },
        )
        return capture


class ReplayObserver:
    """Replaying an existing run must not invoke retrieval or the provider again."""

    @staticmethod
    def provider_factory(settings):
        raise AppError(409, "eval_replay_called_provider", "Replay attempted a new model call.")

    def retrieved(self, result):
        raise AppError(409, "eval_replay_retrieved", "Replay attempted retrieval again.")

    context = retrieved

    def succeeded(self, result):
        pass  # Source-unavailable replay remains application-owned, not a new quality sample.

    def failed(self, error):
        pass


class QueryObserver:
    def __init__(self, runtime, spec, request_hash, request_id):
        self.runtime, self.spec, self.request_hash = runtime, spec, request_hash
        self.request_id, self.started = request_id, time.perf_counter()
        self.row, self.retrieval, self.evidence = None, None, None
        self.hits, self.calls = [], []

    def retrieved(self, result):
        try:
            refs = self.runtime.sources.references(result["hits"])
        except Exception:
            raise AppError(
                503, "eval_source_drift", "Cannot verify captured source identity."
            ) from None
        self.hits = copy.deepcopy(result["hits"])
        self.retrieval = {
            "status": "completed",
            "hits": refs,
            "latency_ms": result["timings_ms"]["total"],
        }

    def context(self, evidence):
        try:
            refs = self.runtime.sources.references(evidence)
        except Exception:
            raise AppError(503, "eval_source_drift", "Cannot verify final context.") from None
        self.evidence = copy.deepcopy(evidence)
        self.final_context = [
            {"evidence_id": item["evidence_id"], "chunk": ref}
            for item, ref in zip(evidence, refs, strict=True)
        ]

    def provider_factory(self, settings):
        if settings_hash(settings) != self.runtime.settings_sha256:
            raise AppError(503, "eval_config_drift", "Settings differ from the pinned runtime.")

        def transport():
            from app.services.gemini import GeminiProvider

            instance = self.runtime.transport_factory(settings)
            if self.runtime.provider_kind == "fake" and isinstance(instance, GeminiProvider):
                raise AppError(503, "eval_live_not_authorized", "Live provider not authorized.")
            return instance

        guarded = GuardedProvider(
            transport,
            self.runtime.ledger,
            self.spec["batch"],
            self.spec["id"] + ":" + self.request_id,
        )
        observer = self

        class Provider:
            def count_tokens(self, payload, deadline):
                return observer.call(guarded, "count_tokens", payload, deadline)

            def generate(self, payload, deadline):
                return observer.call(guarded, "generate", payload, deadline)

        return Provider()

    def call(self, provider, method, payload, deadline):
        try:
            data = json.loads(payload["contents"][0]["parts"][0]["text"])
            if data["question"] != self.spec["question"].strip():
                raise ValueError
            if method == "generate":
                if self.evidence is None or data["evidence"] != [
                    {"evidence_id": item["evidence_id"], "text": item["excerpt"]}
                    for item in self.evidence
                ]:
                    raise ValueError
            elif any(
                item["text"] not in {hit["excerpt"] for hit in self.hits}
                for item in data["evidence"]
            ):
                raise ValueError
        except (KeyError, IndexError, TypeError, ValueError):
            raise AppError(
                503, "eval_payload_drift", "Provider payload differs from capture."
            ) from None
        event = {"method": method, "outcome": "pending", "usage": None}
        self.calls.append(event)
        try:
            result = getattr(provider, method)(payload, deadline)
        except BudgetExceeded:
            event["outcome"] = "blocked_budget"
            raise AppError(
                503, "eval_budget_exhausted", "Approved request budget exhausted."
            ) from None
        except LedgerUnavailable:
            event["outcome"] = "blocked_ledger"
            raise AppError(503, "eval_ledger_unavailable", "Request ledger unavailable.") from None
        except Exception:
            event["outcome"] = "provider_error"
            raise
        event["outcome"] = "returned"
        if (
            method == "generate"
            and isinstance(result, dict)
            and isinstance(result.get("usage"), dict)
        ):
            event["usage"] = {
                key: value
                for key, value in result["usage"].items()
                if key
                in {
                    "promptTokenCount",
                    "candidatesTokenCount",
                    "totalTokenCount",
                    "thoughtsTokenCount",
                    "cachedContentTokenCount",
                }
                and type(value) is int
                and value >= 0
            } or None
        return result

    def succeeded(self, result):
        if self.retrieval is None:
            raise AppError(503, "eval_capture_incomplete", "Retrieval capture is missing.")
        answer = StructuredAnswer.model_validate(
            {
                key: result[key]
                for key in (
                    "answer_status",
                    "claims",
                    "limitations",
                    "missing_information",
                    "conflict_detected",
                )
            }
        ).model_dump()
        self.row = {
            "id": self.spec["id"],
            "status": "completed",
            "retrieval": self.retrieval,
            "answer": answer,
            "final_context": getattr(self, "final_context", []),
            "latency_ms": round((time.perf_counter() - self.started) * 1000, 3),
        }

    def failed(self, error):
        code = getattr(error, "code", "other")
        category = (
            "budget"
            if code in {"eval_budget_exhausted", "eval_ledger_unavailable"}
            else "timeout"
            if code == "model_timeout"
            else "retrieval"
            if code in {"eval_source_drift", "retrieval_unavailable"}
            else "invalid_output"
            if code in {"invalid_model_output", "eval_payload_drift"}
            else "provider"
            if code == "model_unavailable"
            else "other"
        )
        self.row = {
            "id": self.spec["id"],
            "status": "failed",
            "error": category,
            "retrieval": self.retrieval or {"status": "failed", "hits": [], "latency_ms": 0},
            "latency_ms": round((time.perf_counter() - self.started) * 1000, 3),
        }
