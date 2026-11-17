"""BrokerGuard v3 freeze for Test-4: ``final_config_v5``, checked before every Test-4 run and score.

Same mechanism as ``final_config_v4`` (pinned at its own tag): the SHA-256 of every file that
can change an agent, defense or scorer decision, plus the sealed Test-4 release
(``data/adversarial/release_test4``) and the 24 adaptive Test-4 attacks. A Test-4 run or score
refuses to start when any pinned file differs or the (model, configuration) pair is outside
the matrix (decision log 2026-11-15 16:30 and 18:20; freeze 2026-11-17).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.evaluation.final_config_v1 import SKIPPED_PARTS, FrozenConfigError

MANIFEST = Path("configs/final/final_config_v5.json")
FROZEN_TREES = ("src/react_agent", "configs")
ADAPTIVE = "data/adversarial/adaptive_v3/adaptive_test4_attack.jsonl"
FROZEN_FILES = (
    "scripts/run_v3_api_v4.py",
    "scripts/evaluate_v3_v3.py",
    "scripts/freeze_final_config_v5.py",
    "data/adversarial/v3_authoring/spec.json",
    "data/adversarial/v3_authoring/spec_test4.json",
    "data/adversarial/release_test4/seal.json",
    "data/adversarial/release_test4/manifest.json",
    "data/adversarial/release_test4/test4_attack.jsonl",
    "data/adversarial/release_test4/test4_benign_plain.jsonl",
    "data/adversarial/release_test4/test4_benign_auth.jsonl",
    "data/adversarial/release_test4/private/test_oracles.json",
    ADAPTIVE,
)

__all__ = ["ADAPTIVE", "FrozenConfigError", "allowed", "build", "frozen_hashes",
           "manifest_sha256", "verify"]


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
    return {"schema_version": "final_config_v5", "decisions": decisions, "files": files,
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
