"""Compatibility exports; inference implementation moved to backend in Step 06."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.e5_runtime import (  # noqa: E402,F401
    E5Encoder,
    InputTooLong,
    check_lengths,
    prepare_inputs,
)
