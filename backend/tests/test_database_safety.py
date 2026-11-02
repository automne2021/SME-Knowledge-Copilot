"""Guard unit tests: no PostgreSQL, app imports, or model dependencies required."""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from tests import conftest as fixtures
from tests.database_safety import validate_test_database_url

DEV = "postgresql+psycopg://copilot:dummy-password@localhost:5433/copilot"
SAFE = "postgresql+psycopg://copilot:dummy-password@localhost:5433/copilot_test"


@pytest.mark.parametrize(
    ("url", "host", "port", "name"),
    [
        (SAFE, "localhost", 5433, "copilot_test"),
        (SAFE.replace("localhost", "127.0.0.1"), "127.0.0.1", 5433, "copilot_test"),
        (SAFE.replace("localhost:5433", "[::1]:5433"), "::1", 5433, "copilot_test"),
        (SAFE.replace("localhost:5433", "db"), "db", 5432, "copilot_test"),
        (
            SAFE.replace("copilot_test", "copilot_step00_test"),
            "localhost",
            5433,
            "copilot_step00_test",
        ),
        (SAFE.replace("copilot_test", "a" * 58 + "_test"), "localhost", 5433, "a" * 58 + "_test"),
    ],
)
def test_accepts_explicit_local_test_targets(url: str, host: str, port: int, name: str) -> None:
    target = validate_test_database_url(url, DEV)
    assert (target.host, target.port, target.database) == (host, port, name)


@pytest.mark.parametrize(
    "url",
    [
        None,
        "",
        "not-a-url",
        DEV,
        SAFE.replace("copilot_test", "postgres"),
        SAFE.replace("copilot_test", "template1"),
        SAFE.replace("copilot_test", "template0"),
        SAFE.replace("copilot_test", "copilot_test_backup"),
        SAFE.replace("copilot_test", "Copilot_test"),
        SAFE.replace("copilot_test", "a" * 59 + "_test"),
        SAFE.replace("copilot_test", 'evil_test";DROP DATABASE copilot;--'),
        SAFE.replace("copilot_test", "evil%22_test"),
        SAFE.replace("copilot_test", "other/copilot_test"),
        SAFE.replace("copilot_test", "other%2Fcopilot_test"),
        SAFE.replace("copilot_test", "d\u00e9mo_test"),
        SAFE.replace("localhost", "production.example"),
        SAFE.replace("localhost", "localhost.production.example"),
        SAFE.replace("localhost", "127.0.0.2"),
        SAFE.replace("localhost", ""),
        SAFE.replace(":5433", ":0"),
        SAFE.replace(":5433", ":65536"),
        SAFE.replace(":5433", ":bad-port"),
        SAFE.replace("postgresql+psycopg", "sqlite"),
        SAFE.replace("postgresql+psycopg", "postgresql+psycopg2"),
        SAFE.replace("copilot:dummy-password@", ""),
        SAFE.replace("copilot:dummy-password@", "copilot:dummy@password@"),
        SAFE + "?dbname=copilot",
        SAFE + "?host=production.example",
        SAFE + "?service=production",
        SAFE + "?options=-csearch_path=public",
        SAFE + "#fragment",
        SAFE + "?",
        SAFE + "#",
        " " + SAFE,
        SAFE.replace("localhost", "local\nhost"),
    ],
)
def test_rejects_unsafe_or_ambiguous_urls(url: str | None) -> None:
    with pytest.raises(RuntimeError):
        validate_test_database_url(url, DEV)


@pytest.mark.parametrize(
    "development",
    [SAFE, SAFE.replace("localhost", "127.0.0.1"), SAFE.replace("copilot_test", "COPILOT_TEST")],
)
def test_same_database_name_is_rejected_even_with_alias_or_case(development: str) -> None:
    with pytest.raises(RuntimeError, match="differ from development"):
        validate_test_database_url(SAFE, development)


@pytest.mark.parametrize("development", ["", "broken", DEV + "?dbname=copilot_test"])
def test_invalid_development_url_cannot_disable_guard(development: str) -> None:
    with pytest.raises(RuntimeError):
        validate_test_database_url(SAFE, development)


def test_encoded_credentials_and_database_are_returned_without_exposing_password() -> None:
    url = SAFE.replace("dummy-password", "p%40ss%3Fword%23%25").replace(
        "copilot_test", "copilot%5Ftest"
    )
    target = validate_test_database_url(url, DEV)
    assert target.password == "p@ss?word#%"
    assert target.database == "copilot_test"
    assert target.password not in repr(target)


def test_validation_errors_do_not_include_credentials() -> None:
    secret = "sensitive-password-value"
    unsafe = SAFE.replace("dummy-password", secret).replace(":5433", ":invalid")
    with pytest.raises(RuntimeError) as caught:
        validate_test_database_url(unsafe, DEV)
    assert secret not in str(caught.value)
    assert unsafe not in str(caught.value)
    assert caught.value.__suppress_context__


@pytest.mark.parametrize("operation", [fixtures._ensure_database, fixtures._migrate])
@pytest.mark.parametrize(
    "unsafe", [DEV, SAFE + "?dbname=copilot", SAFE.replace("localhost", "remote")]
)
def test_database_operations_validate_before_loading_db_or_migration_tools(
    operation, unsafe
) -> None:
    # These tests also run on system Python with no SQLAlchemy/Alembic installed.
    with pytest.raises(RuntimeError):
        operation(unsafe, DEV)


def test_db_fixture_rejects_unsafe_config_before_create_or_migrate(monkeypatch) -> None:
    config_module = ModuleType("app.core.config")
    config_module.get_settings = lambda: SimpleNamespace(test_database_url=DEV, database_url=DEV)
    monkeypatch.setitem(sys.modules, "app.core.config", config_module)
    ensure = Mock(side_effect=AssertionError("must not create a database"))
    migrate = Mock(side_effect=AssertionError("must not migrate a database"))
    monkeypatch.setattr(fixtures, "_ensure_database", ensure)
    monkeypatch.setattr(fixtures, "_migrate", migrate)
    with pytest.raises(RuntimeError, match="differ from development"):
        next(fixtures.db_engine.__wrapped__())
    ensure.assert_not_called()
    migrate.assert_not_called()
