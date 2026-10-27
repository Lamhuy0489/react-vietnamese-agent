"""R3 freeze: the final configuration manifest and the check every Test run makes first.

The manifest pins the SHA-256 of every file that can change an agent, defense or
scorer decision: the whole ``src/react_agent`` package, ``configs/`` (except the
manifest itself), the Test runners and evaluators, and the data seals. A Test run
refuses to start when any of them differs, so nothing is tuned after the freeze
without a new, recorded manifest.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

MANIFEST = Path("configs/final/final_config_v1.json")
FROZEN_TREES = ("src/react_agent", "configs")
FROZEN_FILES = (
    "scripts/run_adversarial_dev_api_v1.py",
    "scripts/evaluate_adversarial_dev_v1.py",
    "scripts/run_clean_dev_api_v1.py",
    "scripts/evaluate_clean_rebuild_v1.py",
    "data/adversarial/release_v2/seal.json",
    "data/clean/v1_1/manifests/benchmark_manifest.json",
)
SKIPPED_PARTS = {"__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}


class FrozenConfigError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_hashes(root: Path) -> dict[str, str]:
    paths = [p for tree in FROZEN_TREES for p in (root / tree).rglob("*") if p.is_file()]
    paths += [root / name for name in FROZEN_FILES]
    return {
        p.relative_to(root).as_posix(): _sha(p)
        for p in sorted(paths)
        if not SKIPPED_PARTS & set(p.parts) and p.suffix != ".pyc"
        and p.relative_to(root) != MANIFEST
    }


def build(root: Path, decisions: dict[str, Any]) -> dict[str, Any]:
    files = frozen_hashes(root)
    return {"schema_version": "final_config_v1", "decisions": decisions,
            "files": files, "files_sha256": hashlib.sha256(
                json.dumps(files, sort_keys=True).encode()).hexdigest()}


def verify(root: Path) -> dict[str, Any]:
    """The manifest when every frozen file matches it; raises otherwise."""
    path = root / MANIFEST
    if not path.is_file():
        raise FrozenConfigError(f"{MANIFEST} missing: freeze the configuration first (R3)")
    manifest: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    current = frozen_hashes(root)
    changed = sorted(k for k in manifest["files"].keys() | current.keys()
                     if manifest["files"].get(k) != current.get(k))
    if changed:
        raise FrozenConfigError("frozen files differ from the manifest: " + ", ".join(changed[:10]))
    return manifest


def manifest_sha256(root: Path) -> str:
    return _sha(root / MANIFEST)
