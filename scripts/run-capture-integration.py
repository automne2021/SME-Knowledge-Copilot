"""Run scoped integration with existing packages; no model credentials in process."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "backend/.venv/Lib/site-packages"
sys.path[:0] = [str(ROOT / "backend"), str(ROOT), str(PACKAGES)]
# The production parser launches a child interpreter; provide existing packages.
os.environ["PYTHONPATH"] = os.pathsep.join([str(ROOT / "backend"), str(PACKAGES)])
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["LLM_API_KEY"] = ""
os.environ["LLM_FREE_TIER_CONFIRMED"] = "false"
os.environ["LLM_QUOTA_CONFIRMED"] = "false"

if __name__ == "__main__":
    from app.core import config

    safe = config.Settings(
        _env_file=ROOT / ".env",
        llm_api_key=None,
        llm_free_tier_confirmed=False,
        llm_quota_confirmed=False,
    )
    config.get_settings = lambda: safe
    import pytest

    raise SystemExit(
        pytest.main(
            sys.argv[1:]
            or [
                "eval/tests/test_runtime_capture_sql.py",
                "-q",
                "-p",
                "no:cacheprovider",
            ]
        )
    )
