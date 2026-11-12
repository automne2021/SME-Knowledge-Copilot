"""Credential-safe local storage probe; never invokes inference."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(ROOT / "backend"),
    str(ROOT),
    str(ROOT / "backend/.venv/Lib/site-packages"),
]


def main():
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import URL

    from app.core.config import Settings
    from tests.database_safety import validate_test_database_url

    settings = Settings(_env_file=ROOT / ".env")
    target = validate_test_database_url(settings.test_database_url, settings.database_url)
    url = URL.create(
        "postgresql+psycopg",
        username=target.username,
        password=target.password,
        host=target.host,
        port=target.port,
        database=target.database,
    )
    print("Test DB guard: PASS; target=" + target.database)
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    try:
        with engine.connect() as connection:
            print("SELECT1:", connection.scalar(text("select 1")))
            print(
                "DB head:",
                connection.scalar(text("select version_num from alembic_version")),
            )
            print(
                "Pending test jobs:",
                connection.scalar(
                    text(
                        "select count(*) from processing_jobs "
                        "where status in ('queued','retry_wait','running')"
                    )
                ),
            )
            if "--activity" in sys.argv:
                for row in connection.execute(
                    text(
                        "select datname, state, wait_event_type, wait_event, "
                        "split_part(query,' ',1) "
                        "from pg_stat_activity where backend_type='client backend'"
                    )
                ):
                    print("Capture connection:", tuple(row))
    finally:
        engine.dispose()
    if "--capture-summary" in sys.argv:
        capture_url = url.set(database=target.database.removesuffix("_test") + "_capture_test")
        validate_test_database_url(
            capture_url.render_as_string(hide_password=False), settings.database_url
        )
        capture_engine = create_engine(capture_url, connect_args={"connect_timeout": 5})
        try:
            with capture_engine.connect() as connection:
                print(
                    "Capture DB head:",
                    connection.scalar(text("select version_num from alembic_version")),
                )
                for table in (
                    "workspaces",
                    "users",
                    "auth_tokens",
                    "documents",
                    "document_revisions",
                    "source_blocks",
                    "chunks",
                    "processing_jobs",
                    "chat_sessions",
                    "chat_messages",
                    "query_runs",
                    "answer_citations",
                ):
                    print(
                        "Capture rows " + table + ":",
                        connection.scalar(text("select count(*) from " + table)),
                    )
        finally:
            capture_engine.dispose()
        with httpx.Client(base_url=settings.qdrant_url, timeout=5, trust_env=False) as client:
            response = client.get("/collections")
            response.raise_for_status()
            names = [entry["name"] for entry in response.json()["result"]["collections"]]
            print("Remaining final_ collections:", sum(name.startswith("final_") for name in names))
    print(
        "Qdrant ready:",
        httpx.get(settings.qdrant_url + "/readyz", timeout=5).status_code,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 -- never expose connection credentials in errors
        print("Probe failed:", type(exc).__name__)
        raise SystemExit(1) from None
