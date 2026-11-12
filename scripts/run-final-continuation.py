"""Existing-package continuation bootstrap; no app settings on offline paths."""

import multiprocessing
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "backend"), str(ROOT / "backend/.venv/Lib/site-packages")]
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from eval.final_continuation import main

    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Continuation stopped:", type(exc).__name__)
        raise SystemExit(1) from None
