"""Persistent, fail-closed request reservations; no provider or application imports."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import closing, contextmanager
from pathlib import Path

ACTIONS = {"generateContent", "countTokens"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class BudgetExceeded(RuntimeError):
    """No further transport call is permitted under the supplied grant."""


class LedgerUnavailable(RuntimeError):
    """Reservation storage is unavailable; the provider was not called."""


def validate_grant(grant):
    if set(grant) != {"scope_id", "protocol_sha256", "total", "batches"}:
        raise ValueError("Unexpected grant fields")
    if not isinstance(grant["scope_id"], str) or not grant["scope_id"].strip():
        raise ValueError("Missing scope ID")
    digest = grant["protocol_sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or set(digest) - set("0123456789abcdef"):
        raise ValueError("Invalid protocol hash")
    batches = grant["batches"]
    if not isinstance(batches, dict) or not batches:
        raise ValueError("Missing fixed batches")
    for caps in [grant["total"], *batches.values()]:
        if not isinstance(caps, dict) or set(caps) != ACTIONS:
            raise ValueError("Both request actions need explicit caps")
        if any(type(value) is not int or value < 0 for value in caps.values()):
            raise ValueError("Request caps must be nonnegative integers")
    if any(not isinstance(key, str) or not key.strip() for key in batches):
        raise ValueError("Invalid batch ID")
    if any(
        sum(caps[action] for caps in batches.values()) > grant["total"][action]
        for action in ACTIONS
    ):
        raise ValueError("Batch allocations exceed total cap")


class RequestLedger:
    """One SQLite file per approved scope; batches share the same immutable grant.

    Committed reservations are never refunded, including timeouts or process death.
    A grant is a local request allowance, not verification of provider billing/quota.
    """

    def __init__(self, path, grant):
        validate_grant(grant)
        self.path = Path(path)
        self.grant_json = canonical(grant)
        if not self.path.is_file():
            raise ValueError("Create the scope ledger explicitly before attaching")
        with self._connect() as db:
            self._check(db)

    @classmethod
    def create(cls, path, grant):
        validate_grant(grant)
        path = Path(path)
        # Exclusive creation prevents reset by accidentally reusing a scope path.
        with path.open("xb"):
            pass
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE grant_record (value TEXT NOT NULL)")
            db.execute("INSERT INTO grant_record VALUES (?)", (canonical(grant),))
            db.execute(
                "CREATE TABLE reservations (id TEXT PRIMARY KEY, batch TEXT NOT NULL, "
                "action TEXT NOT NULL, query_id TEXT NOT NULL, reserved_at REAL NOT NULL)"
            )
            db.execute("CREATE TABLE runtime_binding (plan_sha256 TEXT NOT NULL)")
        return cls(path, grant)

    @property
    def grant(self):
        return json.loads(self.grant_json)

    @contextmanager
    def _connect(self):
        # mode=rw: never silently recreate a deleted ledger and reset its counts.
        with (
            closing(
                sqlite3.connect(self.path.resolve().as_uri() + "?mode=rw", uri=True, timeout=10)
            ) as db,
            db,
        ):
            yield db

    def _check(self, db):
        rows = db.execute("SELECT value FROM grant_record").fetchall()
        if rows != [(self.grant_json,)]:
            raise ValueError("Ledger grant differs from frozen scope")

    def reserve(self, batch, action, query_id):
        if action not in ACTIONS or batch not in self.grant["batches"]:
            raise ValueError("Unknown action or batch")
        if not isinstance(query_id, str) or not query_id.strip():
            raise ValueError("Missing query ID")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._check(db)
            total = db.execute(
                "SELECT COUNT(*) FROM reservations WHERE action=?", (action,)
            ).fetchone()[0]
            used = db.execute(
                "SELECT COUNT(*) FROM reservations WHERE action=? AND batch=?", (action, batch)
            ).fetchone()[0]
            if total >= self.grant["total"][action] or used >= self.grant["batches"][batch][action]:
                raise BudgetExceeded("Approved request budget exhausted")
            reservation = uuid.uuid4().hex
            db.execute(
                "INSERT INTO reservations VALUES (?, ?, ?, ?, ?)",
                (reservation, batch, action, query_id, time.time()),
            )
        return reservation

    def snapshot(self):
        with self._connect() as db:
            self._check(db)
            rows = db.execute("SELECT batch, action, COUNT(*) FROM reservations GROUP BY 1,2")
            counts = {batch: dict.fromkeys(sorted(ACTIONS), 0) for batch in self.grant["batches"]}
            for batch, action, count in rows:
                counts[batch][action] = count
        return {
            "grant_sha256": fingerprint(self.grant),
            "total": {
                action: sum(c[action] for c in counts.values()) for action in sorted(ACTIONS)
            },
            "batches": counts,
        }

    def bind_runtime(self, plan_sha256):
        """Pin one query/runtime plan for the scope, including after process restart."""
        if (
            not isinstance(plan_sha256, str)
            or len(plan_sha256) != 64
            or set(plan_sha256) - set("0123456789abcdef")
        ):
            raise ValueError("Invalid runtime plan hash")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._check(db)
            rows = db.execute("SELECT plan_sha256 FROM runtime_binding").fetchall()
            if not rows:
                db.execute("INSERT INTO runtime_binding VALUES (?)", (plan_sha256,))
            elif rows != [(plan_sha256,)]:
                raise ValueError("Runtime plan differs from the scope binding")


class GuardedProvider:
    """Wrap the app provider interface; reserve before constructing/calling transport.

    The caller must inject this wrapper into every provider factory in the scoped
    runtime. It does not intercept an unrelated, already running development API.
    """

    def __init__(self, factory, ledger, batch, query_id):
        self.factory, self.ledger = factory, ledger
        self.batch, self.query_id = batch, query_id
        self._provider = None

    def _call(self, action, method, payload, deadline):
        try:
            self.ledger.reserve(self.batch, action, self.query_id)
        except (sqlite3.Error, OSError, ValueError):
            raise LedgerUnavailable("Request ledger unavailable") from None
        if self._provider is None:
            self._provider = self.factory()
        return getattr(self._provider, method)(payload, deadline)

    def count_tokens(self, payload, deadline):
        return self._call("countTokens", "count_tokens", payload, deadline)

    def generate(self, payload, deadline):
        return self._call("generateContent", "generate", payload, deadline)


def request_bound(query_count, top_k=5):
    if type(query_count) is not int or query_count < 0 or type(top_k) is not int or top_k < 1:
        raise ValueError("Invalid query count/top-k")
    return {"generateContent": 2 * query_count, "countTokens": (top_k + 2) * query_count}
