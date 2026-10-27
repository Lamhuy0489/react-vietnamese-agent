"""Small standalone durable writer: no host runner or benchmark dependencies."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from react_agent.serving.structured_api_v1 import canonical


def save_new(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(canonical(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
