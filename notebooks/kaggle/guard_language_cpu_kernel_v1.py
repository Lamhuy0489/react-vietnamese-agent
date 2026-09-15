"""Private CPU tokenizer/logits compatibility worker; no model loading or GPU."""

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


def payload(
    base: ModuleType,
    python: Path,
    project: Path,
    deps: Path | None,
    bundle: Path,
    output: Path,
    *,
    metadata_only: bool = False,
) -> None:
    base.run(
        python,
        project,
        deps,
        SOURCE_COMMIT,
        "scripts/run_phase5_guard_language_native_v1.py",
        "--bundle",
        str(bundle),
        "--output",
        str(output / "language"),
        "--source-commit",
        SOURCE_COMMIT,
        *(["--metadata-only"] if metadata_only else []),
    )


def main() -> None:
    output = Path("/kaggle/working")
    if any((output / n).exists() for n in ("language", "language_bootstrap.json")):
        raise ValueError("fresh CPU outputs required")
    os.environ.update(PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="language-native-cpu-") as temporary:
        scratch = Path(temporary).resolve()
        base = bootstrap(scratch)
        bundle, value = base.manifest(Path("/kaggle/input"), BUNDLE_SHA)
        source_archive(scratch / "source.tar.gz")
        project = scratch / "project"
        base.extract(scratch / "source.tar.gz", project, SOURCE_FILES)
        record: dict[str, Any] = dict(
            protocol="guard_language_cpu_package_v1",
            source_commit=SOURCE_COMMIT,
            source_sha256=SOURCE_FILES,
            archive_sha256=ARCHIVE_SHA,
            dataset_manifest_sha256=BUNDLE_SHA,
            snapshot=value["snapshot"],
            wheel_sha256=value["wheel_sha256"],
            gpu_used=False,
            model_loads=0,
        )
        (output / "language_bootstrap.json").write_text(json.dumps(record, indent=2) + "\n")
        deps, python = scratch / "dependencies", Path(sys.executable)
        try:
            base.install(python, bundle, value, deps)
            payload(base, python, project, deps, bundle, output)
        finally:
            base.verify_tree(project, SOURCE_FILES)


if __name__ == "__main__":
    main()
