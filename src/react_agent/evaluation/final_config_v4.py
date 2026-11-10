"""Study 2 Test-3 freeze: ``final_config_v4``, checked before every Test-3 run and score.

Same mechanism as ``final_config_v3`` (which stays pinned at tag ``final-config-v3``): the
SHA-256 of every file that can change an agent, defense or scorer decision, plus the sealed
Test-3 release (``data/adversarial/release_test3``). A Test-3 run or score refuses to start
when any pinned file differs or the (model, configuration) pair is outside the matrix.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.evaluation.final_config_v1 import SKIPPED_PARTS, FrozenConfigError

MANIFEST = Path("configs/final/final_config_v4.json")
FROZEN_TREES = ("src/react_agent", "configs")
FROZEN_FILES = (
    "scripts/run_v3_api_v1.py",
    "scripts/evaluate_v3_v1.py",
    "scripts/freeze_final_config_v4.py",
    "data/adversarial/v3_authoring/spec.json",
    "data/adversarial/v3_authoring/spec_test3.json",
    "data/adversarial/release_test3/seal.json",
    "data/adversarial/release_test3/test3_attack.jsonl",
    "data/adversarial/release_test3/test3_benign_plain.jsonl",
    "data/adversarial/release_test3/test3_benign_auth.jsonl",
    "data/adversarial/release_test3/private/test_oracles.json",
)
# Earlier manifests are history: they never verify on this tree and are not pinned here.
UNPINNED = (Path("configs/final/final_config_v3.json"),)

__all__ = ["FrozenConfigError", "allowed", "build", "frozen_hashes", "manifest_sha256",
           "verify"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_hashes(root: Path) -> dict[str, str]:
    paths = [p for tree in FROZEN_TREES for p in (root / tree).rglob("*") if p.is_file()]
    paths += [root / name for name in FROZEN_FILES]
    return {
        p.relative_to(root).as_posix(): _sha(p)
        for p in sorted(paths)
        if not SKIPPED_PARTS & set(p.parts) and p.suffix != ".pyc"
        and p.relative_to(root) not in (MANIFEST, *UNPINNED)
    }


def build(root: Path, decisions: dict[str, Any]) -> dict[str, Any]:
    files = frozen_hashes(root)
    return {"schema_version": "final_config_v4", "decisions": decisions, "files": files,
            "files_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def verify(root: Path) -> dict[str, Any]:
    """The manifest when every frozen file matches it; raises otherwise."""
    path = root / MANIFEST
    if not path.is_file():
        raise FrozenConfigError(f"{MANIFEST} missing: freeze the configuration first")
    manifest: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    current = frozen_hashes(root)
    changed = sorted(k for k in manifest["files"].keys() | current.keys()
                     if manifest["files"].get(k) != current.get(k))
    if changed:
        raise FrozenConfigError("frozen files differ from the manifest: " + ", ".join(changed[:10]))
    return manifest


def allowed(manifest: dict[str, Any], model_key: str, config: str) -> bool:
    matrix: dict[str, list[str]] = manifest["decisions"]["test_matrix"]
    return config in matrix.get(model_key, [])


def manifest_sha256(root: Path) -> str:
    return _sha(root / MANIFEST)
