"""Small explicit Qdrant REST adapter; no hidden retry or local vector fallback."""

import re
import uuid

import httpx

from app.services.worker_errors import WorkerError


class QdrantIndex:
    def __init__(self, url, collection, timeout=10):
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", collection):
            raise WorkerError("vector_configuration_error")
        self.collection = collection
        self.client = httpx.Client(base_url=url.rstrip("/"), timeout=timeout, trust_env=False)

    def close(self):
        self.client.close()

    def _request(self, method, suffix="", *, allow_missing=False, **kwargs):
        try:
            response = self.client.request(
                method, f"/collections/{self.collection}{suffix}", **kwargs
            )
        except httpx.TimeoutException as exc:
            raise WorkerError("vector_timeout", True) from exc
        except httpx.RequestError as exc:
            raise WorkerError("vector_unavailable", True) from exc
        if response.status_code == 404 and allow_missing:
            return None
        if response.status_code == 429 or response.status_code >= 500:
            raise WorkerError("vector_unavailable", True)
        if response.status_code >= 400:
            raise WorkerError("vector_configuration_error")
        try:
            data = response.json()
            if data["status"] != "ok":
                raise ValueError
            return data["result"]
        except (KeyError, ValueError, TypeError) as exc:
            raise WorkerError("invalid_vector_response") from exc

    def ensure_collection(self, embedding_hash):
        info = self._request("GET", allow_missing=True)
        if info is None:
            try:
                self._request(
                    "PUT",
                    json={
                        "vectors": {"size": 384, "distance": "Cosine"},
                        "metadata": {"embedding_hash": embedding_hash},
                    },
                )
            except WorkerError:
                # A second worker may have created it concurrently. Re-read and validate.
                if self._request("GET", allow_missing=True) is None:
                    raise
            info = self._request("GET")
        self._validate_collection(info, embedding_hash)
        existing = info.get("payload_schema", {})
        for field in (
            "workspace_id",
            "document_id",
            "revision_id",
            "generation_id",
            "index_version",
        ):
            if field not in existing:
                self._request(
                    "PUT",
                    "/index",
                    params={"wait": "true"},
                    json={"field_name": field, "field_schema": "keyword"},
                )

    def check_collection(self, embedding_hash):
        info = self._request("GET", allow_missing=True)
        if info is None:
            raise WorkerError("vector_unavailable", True)
        self._validate_collection(info, embedding_hash)

    @staticmethod
    def _validate_collection(info, embedding_hash):
        config = info.get("config", {})
        vector = config.get("params", {}).get("vectors", {})
        metadata = config.get("metadata", info.get("metadata", {})) or {}
        if (
            vector.get("size") != 384
            or vector.get("distance") != "Cosine"
            or metadata.get("embedding_hash") != embedding_hash
        ):
            raise WorkerError("vector_fingerprint_mismatch")

    def query(self, vector, workspace_id, generations, index_version, limit):
        result = self._request(
            "POST",
            "/points/query",
            json={
                "query": vector,
                "limit": limit,
                "with_payload": True,
                "with_vector": False,
                "filter": {
                    "must": [
                        {"key": "workspace_id", "match": {"value": str(workspace_id)}},
                        {"key": "generation_id", "match": {"any": [str(g) for g in generations]}},
                        {"key": "index_version", "match": {"value": index_version}},
                    ]
                },
            },
        )
        if not isinstance(result, dict) or not isinstance(result.get("points"), list):
            raise WorkerError("invalid_vector_response")
        if len(result["points"]) > limit:
            raise WorkerError("invalid_vector_response")
        return result["points"]

    def upsert(self, points):
        result = self._request("PUT", "/points", params={"wait": "true"}, json={"points": points})
        if not isinstance(result, dict) or result.get("status") != "completed":
            raise WorkerError("vector_write_incomplete", True)

    @staticmethod
    def generation_filter(generation_id):
        return {"must": [{"key": "generation_id", "match": {"value": str(generation_id)}}]}

    def scroll(self, generation_id=None):
        offset = None
        seen_offsets = set()
        while True:
            body = {"limit": 256, "with_payload": True, "with_vector": False}
            if generation_id is not None:
                body["filter"] = self.generation_filter(generation_id)
            if offset is not None:
                body["offset"] = offset
            result = self._request("POST", "/points/scroll", json=body)
            if not isinstance(result, dict) or not isinstance(result.get("points"), list):
                raise WorkerError("invalid_vector_response")
            yield from result["points"]
            offset = result.get("next_page_offset")
            if offset is None:
                break
            if str(offset) in seen_offsets:
                raise WorkerError("invalid_vector_response")
            seen_offsets.add(str(offset))

    def verify(self, generation_id, expected):
        actual = {}
        for point in self.scroll(generation_id):
            try:
                point_id = str(uuid.UUID(str(point["id"])))
            except (KeyError, ValueError, TypeError) as exc:
                raise WorkerError("vector_manifest_mismatch") from exc
            if (
                point_id not in expected
                or point_id in actual
                or point.get("payload") != expected[point_id]
            ):
                raise WorkerError("vector_manifest_mismatch")
            actual[point_id] = True
        if set(actual) != set(expected):
            raise WorkerError("vector_manifest_mismatch")

    def delete_generation(self, generation_id):
        result = self._request(
            "POST",
            "/points/delete",
            params={"wait": "true"},
            json={"filter": self.generation_filter(generation_id)},
        )
        if not isinstance(result, dict) or result.get("status") != "completed":
            raise WorkerError("vector_write_incomplete", True)
        if next(self.scroll(generation_id), None) is not None:
            raise WorkerError("vector_cleanup_incomplete", True)
