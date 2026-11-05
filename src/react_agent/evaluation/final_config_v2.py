"""Rebuild A freeze v2: the manifest every Test-2 / clean robustness Test run checks first.

Same mechanism as ``final_config_v1`` (which stays pinned and untouched): the SHA-256 of
every file that can change an agent, defense or scorer decision. v2 adds the rebuild-A
runners and evaluators, the Test-2 seal and the RQ3 robustness seal. A Test run refuses
to start when any pinned file differs, so nothing is tuned after the freeze without a
new, recorded manifest.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.evaluation.final_config_v1 import SKIPPED_PARTS, FrozenConfigError

MANIFEST = Path("configs/final/final_config_v2.json")
FROZEN_TREES = ("src/react_agent", "configs")
FROZEN_FILES = (
    "scripts/run_clean_dev_api_v1.py",
    "scripts/evaluate_clean_rebuild_v1.py",
    "scripts/run_clean_robustness_api_v1.py",
    "scripts/evaluate_clean_robustness_v1.py",
    "scripts/evaluate_side_effect_harm_v1.py",
    "data/adversarial/release_test2/seal.json",
    "data/clean/robustness_v1/seal.json",
    "data/clean/v1_1/manifests/benchmark_manifest.json",
)

__all__ = ["FrozenConfigError", "build", "frozen_hashes", "manifest_sha256", "verify"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_hashes(root: Path, extra_files: tuple[str, ...] = ()) -> dict[str, str]:
    paths = [p for tree in FROZEN_TREES for p in (root / tree).rglob("*") if p.is_file()]
    paths += [root / name for name in (*FROZEN_FILES, *extra_files)]
    return {
        p.relative_to(root).as_posix(): _sha(p)
        for p in sorted(paths)
        if not SKIPPED_PARTS & set(p.parts) and p.suffix != ".pyc"
        and p.relative_to(root) != MANIFEST
    }


def build(root: Path, decisions: dict[str, Any],
          extra_files: tuple[str, ...] = ()) -> dict[str, Any]:
    files = frozen_hashes(root, extra_files)
    return {"schema_version": "final_config_v2", "decisions": decisions,
            "extra_files": list(extra_files), "files": files,
            "files_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def verify(root: Path) -> dict[str, Any]:
    """The manifest when every frozen file matches it; raises otherwise."""
    path = root / MANIFEST
    if not path.is_file():
        raise FrozenConfigError(f"{MANIFEST} missing: freeze the configuration first")
    manifest: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    current = frozen_hashes(root, tuple(manifest.get("extra_files", ())))
    changed = sorted(k for k in manifest["files"].keys() | current.keys()
                     if manifest["files"].get(k) != current.get(k))
    if changed:
        raise FrozenConfigError("frozen files differ from the manifest: " + ", ".join(changed[:10]))
    return manifest


def manifest_sha256(root: Path) -> str:
    return _sha(root / MANIFEST)
