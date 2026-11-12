"""Isolated browser harness bootstrap; existing packages, no download/install."""

import multiprocessing
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT), str(ROOT / "backend/.venv/Lib/site-packages")]
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from eval.browser_e2e import main

    raise SystemExit(main())
