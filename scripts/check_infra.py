"""Read-only PostgreSQL/Qdrant probe; run with the backend virtualenv Python."""

import json
import sys
from pathlib import Path
from urllib.request import urlopen

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

    from app.core.config import get_settings

    settings = get_settings()
    checks = {}
    engine = create_engine(settings.database_url, connect_args={"connect_timeout": 5})
    try:
        with engine.connect() as connection:
            checks["postgres"] = {
                "ready": connection.execute(text("SELECT 1")).scalar() == 1,
                "server_version": connection.execute(text("SHOW server_version")).scalar(),
            }
    except SQLAlchemyError as exc:
        checks["postgres"] = {"ready": False, "error_type": type(exc).__name__}
    finally:
        engine.dispose()

    base_url = settings.qdrant_url.rstrip("/")
    try:
        with urlopen(f"{base_url}/readyz", timeout=5) as response:
            ready = response.status == 200
        with urlopen(f"{base_url}/", timeout=5) as response:
            metadata = json.load(response)
        with urlopen(f"{base_url}/collections", timeout=5) as response:
            collections = json.load(response)["result"]["collections"]
        checks["qdrant"] = {
            "ready": ready,
            "version": metadata["version"],
            "collection_count": len(collections),
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        checks["qdrant"] = {"ready": False, "error_type": type(exc).__name__}

    print(json.dumps(checks, indent=2))
    return 0 if all(item["ready"] for item in checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
