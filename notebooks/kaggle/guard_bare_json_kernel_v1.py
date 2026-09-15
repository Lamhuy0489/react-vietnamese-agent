"""Private synthetic observer worker with a complete embedded, hash-bound source package."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

SOURCE_COMMIT = "__SOURCE_COMMIT__"
BASE_SOURCE = "__BASE_SOURCE__"
BASE_SHA = "__BASE_SHA__"
ARCHIVE = "__ARCHIVE__"
ARCHIVE_SHA = "__ARCHIVE_SHA__"
BUNDLE_SHA = "__BUNDLE_SHA__"
SOURCE_FILES: dict[str, str] = {}  # __SOURCE_FILES__


def bootstrap(scratch: Path) -> ModuleType:
    data = base64.b64decode(BASE_SOURCE, validate=True)
    if hashlib.sha256(data).hexdigest() != BASE_SHA:
        raise ValueError("bootstrap source mismatch")
    path = scratch / "bootstrap.py"
    path.write_bytes(data)
    spec = importlib.util.spec_from_file_location("observer_bootstrap", path)
    if spec is None or spec.loader is None:
        raise ValueError("bootstrap unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_archive(path: Path) -> None:
    data = base64.b64decode(ARCHIVE, validate=True)
    if hashlib.sha256(data).hexdigest() != ARCHIVE_SHA:
        raise ValueError("source archive mismatch")
    path.write_bytes(data)


def native_payload(
    base: ModuleType,
    python: Path,
    project: Path,
    deps: Path | None,
    guard: Path,
    snapshot: Path,
    output: Path,
    input_root: Path,
) -> None:
    candidates = [
        p.parent
        for p in input_root.rglob("config.json")
        if p.parent.parts[-4:] == ("qwen2.5", "transformers", "7b-instruct", "1")
    ]
    if len(candidates) != 1:
        raise ValueError("one pinned agent mount required")
    base.run(
        python,
        project,
        deps,
        SOURCE_COMMIT,
        "scripts/collect_phase5_tokenizer_metadata.py",
        "--agent-path",
        str(candidates[0]),
        "--guard-path",
        str(guard),
        "--output",
        str(output / "tokenizers"),
    )
    base.run(
        python,
        project,
        deps,
        SOURCE_COMMIT,
        "scripts/run_phase5_guard_bare_json_probe_v1.py",
        "--backend",
        "hf",
        "--input-root",
        str(input_root),
        "--guard-path",
        str(guard),
        "--snapshot",
        str(snapshot),
        "--output",
        str(output / "observer"),
    )
    base.run(
        python,
        project,
        deps,
        SOURCE_COMMIT,
        "scripts/audit_phase5_guard_bare_json_probe_v1.py",
        "--probe",
        str(output / "observer"),
        "--source-commit",
        SOURCE_COMMIT,
        "--snapshot",
        str(snapshot),
        "--tokenizers",
        str(output / "tokenizers"),
        "--publishers",
        str(project / "docs/evaluation/publisher_policy_v1"),
        "--output",
        str(output / "native_audit.json"),
    )


def main() -> None:
    output, input_root = Path("/kaggle/working"), Path("/kaggle/input")
    if len(SOURCE_COMMIT) != 40 or any(c not in "0123456789abcdef" for c in SOURCE_COMMIT):
        raise ValueError("frozen source required")
    for name in ("observer_bootstrap.json", "observer", "tokenizers", "native_audit.json"):
        if (output / name).exists() or (output / name).is_symlink():
            raise ValueError("fresh worker outputs required")
    os.environ.update(PAIR_SOURCE_COMMIT=SOURCE_COMMIT, PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="observer-native-") as temporary:
        scratch = Path(temporary).resolve()
        base = bootstrap(scratch)
        bundle, value = base.manifest(input_root, BUNDLE_SHA)
        source_archive(scratch / "source.tar.gz")
        project, guard = scratch / "project", scratch / "guard"
        base.extract(scratch / "source.tar.gz", project, SOURCE_FILES)
        base.materialize(
            bundle,
            "guard-model.tar",
            value["model_archive_sha256"],
            "model.safetensors",
            guard,
            {f["name"]: f["sha256"] for f in value["snapshot"]["files"]},
        )
        record: dict[str, Any] = dict(
            protocol="guard_bare_json_package_v1",
            source_commit=SOURCE_COMMIT,
            source_sha256=SOURCE_FILES,
            source_archive_sha256=ARCHIVE_SHA,
            bundle_manifest_sha256=BUNDLE_SHA,
            snapshot=value["snapshot"],
            wheel_sha256=value["wheel_sha256"],
            phase5_accepted=False,
        )
        (output / "observer_bootstrap.json").write_text(json.dumps(record, indent=2) + "\n")
        deps, python = scratch / "dependencies", Path(sys.executable)
        try:
            base.install(python, bundle, value, deps)
            base.run(python, project, deps, SOURCE_COMMIT, "scripts/preflight_clean_worker.py")
            snapshot = scratch / "snapshot.json"
            snapshot.write_text(json.dumps(value["snapshot"]))
            native_payload(base, python, project, deps, guard, snapshot, output, input_root)
        finally:
            base.verify_tree(project, SOURCE_FILES)


if __name__ == "__main__":
    main()
