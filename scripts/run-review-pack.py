"""Standard-library-only review CLI for Python installations with isolated sys.path."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    from eval.review_pack import main

    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Review command stopped:", type(exc).__name__)
        raise SystemExit(1) from None
