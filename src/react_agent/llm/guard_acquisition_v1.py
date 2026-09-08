"""Pure verification of independently recorded publisher hashes; no network I/O."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from react_agent.foundation.artifacts import Immutable
from react_agent.llm.guard_snapshot_v1 import ALLOWED, REQUIRED, GuardSnapshot, describe_snapshot


class UpstreamFile(Immutable):
    name: str
    size: int = Field(gt=0, strict=True)
    git_blob_sha1: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def safe(self) -> Self:
        if self.name not in ALLOWED or (self.git_blob_sha1 is None) == (self.sha256 is None):
            raise ValueError("allowlisted file with exactly one upstream hash required")
        if self.name == "model.safetensors" and self.sha256 is None:
            raise ValueError("weights require publisher LFS SHA-256")
        return self


class UpstreamSnapshot(Immutable):
    model_id: Literal["Qwen/Qwen2.5-1.5B-Instruct"]
    revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    metadata_url: str
    access_date: str
    files: tuple[UpstreamFile, ...]

    @model_validator(mode="after")
    def complete(self) -> Self:
        names = [f.name for f in self.files]
        if names != sorted(set(names)) or not (REQUIRED | {"LICENSE"}).issubset(names):
            raise ValueError("complete sorted publisher inventory including license required")
        expected = (
            f"https://huggingface.co/api/models/{self.model_id}/revision/{self.revision}?blobs=true"
        )
        if self.metadata_url != expected:
            raise ValueError("official immutable metadata URL required")
        return self

    def url(self, entry: UpstreamFile) -> str:
        if entry not in self.files:
            raise ValueError("file not in pinned inventory")
        return f"https://huggingface.co/{self.model_id}/resolve/{self.revision}/{entry.name}"


def verify_upstream_file(path: Path, expected: UpstreamFile) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size != expected.size:
        raise ValueError("download type/size mismatch")
    sha256 = hashlib.sha256()
    # Git object's SHA-1 is the publisher's legacy content address, not a new
    # security algorithm choice. Every admitted local file also gets SHA-256.
    git_blob = hashlib.sha1(usedforsecurity=False)
    git_blob.update(f"blob {expected.size}\0".encode())
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha256.update(block)
            git_blob.update(block)
    if expected.sha256 is not None and sha256.hexdigest() != expected.sha256:
        raise ValueError("publisher SHA-256 mismatch")
    if expected.git_blob_sha1 is not None and git_blob.hexdigest() != expected.git_blob_sha1:
        raise ValueError("publisher Git blob mismatch")
    return sha256.hexdigest()


def verify_acquisition(root: Path, upstream: UpstreamSnapshot) -> GuardSnapshot:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("materialized snapshot required")
    if sorted(p.name for p in root.iterdir()) != [f.name for f in upstream.files]:
        raise ValueError("download inventory mismatch")
    for entry in upstream.files:
        verify_upstream_file(root / entry.name, entry)
    return describe_snapshot(root, upstream.revision)
