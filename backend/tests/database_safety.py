"""Fail closed before test fixtures connect to or migrate a database."""

import re
from dataclasses import dataclass, field
from urllib.parse import unquote, urlsplit

LOCAL_TEST_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "db"})
TEST_DATABASE_NAME = re.compile(r"[a-z][a-z0-9_]*_test", re.ASCII)


@dataclass(frozen=True)
class SafeDatabaseTarget:
    host: str
    port: int
    database: str
    username: str
    password: str | None = field(repr=False)


def _parse_url(value: str | None, setting: str) -> SafeDatabaseTarget:
    # Do not echo URLs or parser exceptions: either may contain credentials.
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        raise RuntimeError(f"{setting}: required explicit PostgreSQL URL.")
    try:
        parsed = urlsplit(value)
        port = parsed.port if parsed.port is not None else 5432
        host = parsed.hostname
        username = unquote(parsed.username or "")
        database = unquote(parsed.path.removeprefix("/"))
        if (
            parsed.scheme != "postgresql+psycopg"
            or not host
            or not username
            or parsed.netloc.count("@") != 1
            or not 1 <= port <= 65535
            or not parsed.path.startswith("/")
            or not database
            or "/" in database
            or parsed.query
            or parsed.fragment
            or "?" in value
            or "#" in value
        ):
            raise ValueError
        password = unquote(parsed.password) if parsed.password is not None else None
    except (ValueError, UnicodeError):
        raise RuntimeError(
            f"{setting}: require postgresql+psycopg, explicit user/host/database, "
            "valid port, and no query parameters or fragment."
        ) from None
    return SafeDatabaseTarget(host, port, database, username, password)


def validate_test_database_url(test_url: str | None, development_url: str) -> SafeDatabaseTarget:
    """Only local test targets; never infer permission from a connection attempt."""
    target = _parse_url(test_url, "TEST_DATABASE_URL")
    development = _parse_url(development_url, "DATABASE_URL")
    if target.database.casefold() == development.database.casefold():
        raise RuntimeError("TEST_DATABASE_URL: database must differ from development.")
    if len(target.database) > 63 or TEST_DATABASE_NAME.fullmatch(target.database) is None:
        raise RuntimeError(
            "TEST_DATABASE_URL: use a lowercase ASCII database name ending in _test "
            "(at most 63 characters)."
        )
    if target.host not in LOCAL_TEST_HOSTS:
        raise RuntimeError("TEST_DATABASE_URL: only loopback or Compose host db is allowed.")
    return target
