"""Persistent model subprocess with bounded startup/batch waits and strict validation."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import multiprocessing
import os
import time
from pathlib import Path

from app.services.chunking import CHUNKER_VERSION
from app.services.parsing import PARSER_VERSION
from app.services.worker_errors import WorkerError

MODEL_FILES = (
    "config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentencepiece.bpe.model",
)


def content_hash(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def frozen_profile(settings) -> dict:
    from huggingface_hub import snapshot_download

    try:
        snapshot = Path(
            snapshot_download(
                settings.embedding_model,
                revision=settings.embedding_revision,
                allow_patterns=list(MODEL_FILES),
                cache_dir=str(settings.hf_home / "hub"),
                local_files_only=True,
                token=False,
            )
        )
        hashes = {}
        for name in MODEL_FILES:
            with (snapshot / name).open("rb") as stream:
                hashes[name] = hashlib.file_digest(stream, "sha256").hexdigest()
        runtime = {
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "tokenizers")
        }
    except Exception as exc:
        raise WorkerError("embedding_configuration_error") from exc
    fingerprint = {
        "provider": "local",
        "model": settings.embedding_model,
        "revision": settings.embedding_revision,
        "dimension": 384,
        "device": "cpu",
        "dtype": "float32",
        "pooling": "masked_mean",
        "normalize": "l2",
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
        "max_input_tokens": 512,
        "files": hashes,
        "runtime": runtime,
    }
    chunking = {
        "version": CHUNKER_VERSION,
        "size_tokens": settings.chunk_size_tokens,
        "overlap_tokens": settings.chunk_overlap_tokens,
        "max_chunks": settings.max_document_chunks,
    }
    index = {"embedding": fingerprint, "parser": PARSER_VERSION, "chunking": chunking}
    return {
        "snapshot": str(snapshot),
        "embedding_fingerprint": fingerprint,
        "embedding_hash": content_hash(fingerprint),
        "parser_version": PARSER_VERSION,
        "chunking_config": chunking,
        "index_version": content_hash(index),
        "collection_name": settings.qdrant_collection,
    }


def validate_vectors(vectors, count: int) -> None:
    if not isinstance(vectors, list) or len(vectors) != count:
        raise WorkerError("invalid_embedding")
    for vector in vectors:
        if (
            not isinstance(vector, list)
            or len(vector) != 384
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in vector
            )
        ):
            raise WorkerError("invalid_embedding")
        if not math.isclose(sum(value * value for value in vector), 1.0, abs_tol=0.002):
            raise WorkerError("invalid_embedding")


def _model_process(connection, snapshot, threads):
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    try:
        from app.services.e5_runtime import E5Encoder

        encoder = E5Encoder(Path(snapshot), threads)
        connection.send({"ready": True})
        while True:
            message = connection.recv()
            if message is None:
                break
            texts, kind = message["texts"], message["kind"]
            try:
                vectors = encoder.encode(texts, kind, len(texts)).tolist()
                connection.send({"vectors": vectors})
            except Exception as exc:
                code = (
                    "embedding_oom" if "OutOfMemory" in type(exc).__name__ else "invalid_embedding"
                )
                connection.send({"error": code})
    except (EOFError, BrokenPipeError):
        pass
    except Exception:
        try:
            connection.send({"error": "embedding_configuration_error"})
        except (EOFError, BrokenPipeError):
            pass
    finally:
        connection.close()


class LocalEmbedder:
    def __init__(self, profile, settings):
        self.profile, self.settings = profile, settings
        self.process = self.connection = None
        self.load_seconds = 0.0

    def _receive(self, deadline=None):
        try:
            timeout = self.settings.embedding_timeout_seconds
            if deadline is not None:
                timeout = max(0, min(timeout, deadline - time.monotonic()))
            if not self.connection.poll(timeout):
                self.close()
                raise WorkerError("embedding_timeout", retryable=True)
            payload = self.connection.recv()
        except (EOFError, BrokenPipeError, OSError) as exc:
            self.close()
            raise WorkerError("embedding_process_failed", retryable=True) from exc
        if "error" in payload:
            raise WorkerError(payload["error"])
        return payload

    def encode(self, texts, kind="passage", deadline=None):
        if kind not in {"query", "passage"}:
            raise WorkerError("embedding_configuration_error")
        if self.process is None:
            started = time.perf_counter()
            context = multiprocessing.get_context("spawn")
            self.connection, child = context.Pipe()
            self.process = context.Process(
                target=_model_process,
                args=(child, self.profile["snapshot"], self.settings.embedding_threads),
                daemon=True,
            )
            self.process.start()
            child.close()
            if not self._receive(deadline).get("ready"):
                raise WorkerError("embedding_configuration_error")
            self.load_seconds = time.perf_counter() - started
        try:
            self.connection.send({"texts": texts, "kind": kind})
        except (EOFError, BrokenPipeError, OSError) as exc:
            self.close()
            raise WorkerError("embedding_process_failed", retryable=True) from exc
        vectors = self._receive(deadline)["vectors"]
        validate_vectors(vectors, len(texts))
        return vectors

    def encode_query(self, query, deadline=None):
        return self.encode([query], kind="query", deadline=deadline)[0]

    def close(self):
        if self.process:
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(timeout=5)
            self.process.close()
        if self.connection:
            self.connection.close()
        self.process = self.connection = None
