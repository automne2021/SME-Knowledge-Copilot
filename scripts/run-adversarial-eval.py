"""Existing-package AT-R14 bootstrap; offline cache, no dependency installation."""

import multiprocessing
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "backend"), str(ROOT / "backend/.venv/Lib/site-packages")]
os.environ.update(
    HF_HUB_OFFLINE="1",
    TRANSFORMERS_OFFLINE="1",
    PYTHONDONTWRITEBYTECODE="1",
    TOKENIZERS_PARALLELISM="false",
)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from eval.adversarial_eval import main

    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Adversarial evaluation stopped:", type(exc).__name__)
        raise SystemExit(1) from None
