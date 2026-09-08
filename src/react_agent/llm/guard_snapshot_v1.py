"""Content-bound, materialized Qwen guard snapshot; never downloads model files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from react_agent.foundation.artifacts import Immutable, canonical_json
from react_agent.foundation.normalization import text_hash

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
CANDIDATE_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
REQUIRED = frozenset(
    {
        "config.json",
        "generation_config.json",
        "merges.txt",
        "model.safetensors",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
    }
)
ALLOWED = REQUIRED | {"README.md", "LICENSE", ".gitattributes"}


class SnapshotFile(Immutable):
    name: str
    size: int = Field(gt=0, strict=True)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def allowed_name(self) -> Self:
        if self.name not in ALLOWED:
            raise ValueError("unsupported snapshot file")
        return self


class GuardSnapshot(Immutable):
    schema_version: Literal["qwen_guard_snapshot_v1"] = "qwen_guard_snapshot_v1"
    model_id: Literal["Qwen/Qwen2.5-1.5B-Instruct"] = "Qwen/Qwen2.5-1.5B-Instruct"
    upstream_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    files: tuple[SnapshotFile, ...]

    @model_validator(mode="after")
    def inventory(self) -> Self:
        names = [item.name for item in self.files]
        if names != sorted(set(names)) or not REQUIRED.issubset(names):
            raise ValueError("complete sorted unique snapshot inventory required")
        return self

    @property
    def sha256(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))

    @property
    def model_revision(self) -> str:
        # Warm guard/cache identity binds bytes, not just a caller-provided revision label.
        return f"hf:{self.upstream_revision};snapshot-sha256:{self.sha256}"


def snapshot_files(root: Path) -> tuple[SnapshotFile, ...]:
    """Require a flat materialized mount; reject cache symlinks and extra files."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("materialized snapshot directory required")
    paths = sorted(root.iterdir())
    if not REQUIRED.issubset(p.name for p in paths) or len(paths) > len(ALLOWED):
        raise ValueError("incomplete or unexpected snapshot inventory")
    records = []
    for path in paths:
        if path.name not in ALLOWED or path.is_symlink() or not path.is_file():
            raise ValueError("unsupported snapshot entry")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        records.append(SnapshotFile(name=path.name, size=path.stat().st_size, sha256=digest))
    return tuple(records)


def verify_snapshot(root: Path, expected: GuardSnapshot) -> None:
    if snapshot_files(root) != expected.files:
        raise ValueError("snapshot content mismatch")
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    if (
        config.get("model_type") != "qwen2"
        or config.get("architectures") != ["Qwen2ForCausalLM"]
        or "quantization_config" in config
        or "auto_map" in config
    ):
        raise ValueError("only native unquantized Qwen2 causal models supported")


def describe_snapshot(root: Path, upstream_revision: str) -> GuardSnapshot:
    """Hash a trusted acquisition; this alone does NOT authenticate its publisher."""
    snapshot = GuardSnapshot(upstream_revision=upstream_revision, files=snapshot_files(root))
    verify_snapshot(root, snapshot)
    return snapshot
