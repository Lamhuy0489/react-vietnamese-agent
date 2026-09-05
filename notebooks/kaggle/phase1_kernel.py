"""Thin Kaggle entrypoint for the frozen Phase 1 source bundle."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tarfile
from pathlib import Path

INPUT_ROOT = Path("/kaggle/input")
WORK_ROOT = Path("/kaggle/working")
PROJECT_ROOT = WORK_ROOT / "react-vietnamese-agent"
MODEL_SOURCE = "qwen-lm/qwen2.5/transformers/3b-instruct/1"
EXPECTED_MODEL_SUFFIX = Path("qwen2.5/transformers/3b-instruct/1")


def find_unique(name: str) -> Path:
    matches = list(INPUT_ROOT.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {name!r} under {INPUT_ROOT}, found {matches}")
    return matches[0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    resolved_destination = destination.resolve()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            target = (destination / member.name).resolve()
            if resolved_destination not in target.parents and target != resolved_destination:
                raise RuntimeError(f"unsafe archive member: {member.name}")
        tar.extractall(destination)  # noqa: S202 - paths validated immediately above


def run(*arguments: str) -> None:
    subprocess.run(  # noqa: S603 - fixed interpreter and repository scripts
        [sys.executable, *arguments], cwd=PROJECT_ROOT, check=True
    )


archive = find_unique("react-vietnamese-agent-phase1.tar.gz")
safe_extract(archive, PROJECT_ROOT)
model_candidates = [path for path in INPUT_ROOT.rglob("3b-instruct/1") if path.is_dir()]
model_candidates = [
    path for path in model_candidates if str(path).endswith(str(EXPECTED_MODEL_SUFFIX))
]
if len(model_candidates) != 1:
    raise RuntimeError(f"expected one frozen model path, found {model_candidates}")
model_path = model_candidates[0]

bundle_info = {
    "archive_sha256": sha256(archive),
    "model_source": MODEL_SOURCE,
    "model_path": str(model_path),
}
(WORK_ROOT / "kaggle_bundle_info.json").write_text(
    json.dumps(bundle_info, indent=2) + "\n", encoding="utf-8"
)

run("scripts/build_smoke_environment.py")
run("scripts/validate_smoke_data.py")
run("scripts/verify_phase1.py")
run(
    "scripts/run_hf_smoke.py",
    "--model-path",
    str(model_path),
    "--task-id",
    "smoke_001",
    "--output",
    str(WORK_ROOT / "phase1_preflight"),
)
run(
    "scripts/run_hf_smoke.py",
    "--model-path",
    str(model_path),
    "--output",
    str(WORK_ROOT / "phase1_real_model"),
)
run("scripts/validate_phase1_run.py", str(WORK_ROOT / "phase1_real_model"))
print("PHASE1_KAGGLE_SMOKE_COMPLETE")
