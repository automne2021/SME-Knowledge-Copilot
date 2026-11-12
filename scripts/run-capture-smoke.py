"""Bootstrap existing local packages; preserve the private model configuration."""

import multiprocessing
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT), str(ROOT / "backend/.venv/Lib/site-packages")]
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from eval.run_capture_smoke import main

    raise SystemExit(main())
