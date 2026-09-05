"""Location of the generated read-only SQLite fixture."""

from __future__ import annotations

from pathlib import Path


class DatabaseStore:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        if not self.path.is_file():
            raise FileNotFoundError(f"SQLite fixture not found: {self.path}")
