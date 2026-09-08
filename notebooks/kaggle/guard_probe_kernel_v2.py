"""Stdlib-only private guard bootstrap v2 with commit-bound PAX adaptation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

EXPECTED_MANIFEST_SHA256 = "__BUNDLE_MANIFEST_SHA256__"
BOOTSTRAP_COMMIT = "__BOOTSTRAP_COMMIT__"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def relative_name(name: str) -> str:
    path = PurePosixPath(name)
    if (
        not name
        or not path.parts
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in name
        or path.as_posix() != name
        or ":" in name
        or any(p.casefold() in {"private", "pool", "reviews", "test.jsonl"} for p in path.parts)
        or "credential" in name.casefold()
    ):
        raise ValueError("unsafe bundle path")
    return name


def verify_tree(root: Path, expected: dict[str, str]) -> None:
    if root.is_symlink() or not root.is_dir() or not expected:
        raise ValueError("materialized nonempty bundle required")
    for name in expected:
        relative_name(name)
    directories = {str(parent) for name in expected for parent in PurePosixPath(name).parents}
    actual = {}
    for path in root.rglob("*"):
        name = relative_name(path.relative_to(root).as_posix())
        if path.is_symlink():
            raise ValueError("bundle links prohibited")
        if path.is_dir():
            if name not in directories:
                raise ValueError("unexpected bundle directory")
        elif path.is_file():
            actual[name] = digest(path)
        else:
            raise ValueError("unsupported bundle entry")
    if actual != expected:
        raise ValueError("exact bundle inventory/hash mismatch")


def extract(archive: Path, destination: Path, expected: dict[str, str]) -> None:
    if destination.exists():
        raise ValueError("fresh extraction target required")
    for name in expected:
        relative_name(name)
    with tarfile.open(archive) as stream:
        files = {}
        directories = {str(parent) for name in expected for parent in PurePosixPath(name).parents}
        seen = set()
        for item in stream.getmembers():
            name = relative_name(item.name.rstrip("/") if item.isdir() else item.name)
            if name in seen or not (item.isfile() or item.isdir()):
                raise ValueError("duplicate or unsafe archive member")
            seen.add(name)
            if item.isfile():
                files[name] = item
            elif name not in directories:
                raise ValueError("unexpected archive directory")
        if set(files) != set(expected):
            raise ValueError("archive inventory mismatch")
        destination.mkdir(parents=True)
        for name, item in files.items():
            source = stream.extractfile(item)
            if source is None:
                raise ValueError("archive content unavailable")
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
    verify_tree(destination, expected)


def materialize(
    bundle: Path,
    archive_name: str,
    archive_hash: str,
    marker: str,
    target: Path,
    expected: dict[str, str],
    source_commit: str | None = None,
) -> None:
    archive = bundle / archive_name
    if archive.is_file():
        if archive.is_symlink() or digest(archive) != archive_hash:
            raise ValueError("archive hash mismatch")
        extract(archive, target, expected)
    else:
        candidates = [p.parent for p in bundle.rglob(marker)]
        if len(candidates) != 1:
            raise ValueError("unique expanded bundle required")
        expanded = candidates[0]
        sidecar = expanded / "pax_global_header"
        inventory = dict(expected)
        if sidecar.exists() or sidecar.is_symlink():
            if (
                archive_name != "source.tar.gz"
                or source_commit is None
                or len(source_commit) != 40
                or any(c not in "0123456789abcdef" for c in source_commit)
                or "pax_global_header" in expected
            ):
                raise ValueError("unbound PAX sidecar")
            payload = ("52 comment=" + source_commit + "\n").encode("ascii")
            inventory["pax_global_header"] = hashlib.sha256(payload).hexdigest()
        verify_tree(expanded, inventory)
        shutil.copytree(expanded, target, ignore=shutil.ignore_patterns("pax_global_header"))
        verify_tree(target, expected)


def manifest(input_root: Path, expected_digest: str) -> tuple[Path, dict[str, Any]]:
    paths = list(input_root.rglob("guard_bundle.json"))
    if len(paths) != 1 or paths[0].is_symlink() or digest(paths[0]) != expected_digest:
        raise ValueError("unique hash-bound guard bundle manifest required")
    value: dict[str, Any] = json.loads(paths[0].read_text())
    return paths[0].parent, value


def run(
    python: Path,
    project: Path,
    dependencies: Path | None,
    commit: str,
    *arguments: str,
) -> None:
    environment = os.environ.copy()
    for key in ("VIRTUAL_ENV", "PYTHONHOME", "PILOT_DEPENDENCY_DIR"):
        environment.pop(key, None)
    environment.update(
        PYTHONPATH=str(project / "src") + (os.pathsep + str(dependencies) if dependencies else ""),
        PYTHONNOUSERSITE="1",
        PYTHONDONTWRITEBYTECODE="1",
        FROZEN_GIT_COMMIT=commit,
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    subprocess.run(  # noqa: S603 - fixed interpreter/repository scripts, no shell
        [str(python), *arguments],
        cwd=project,
        env=environment,
        check=True,
    )


def install(python: Path, bundle: Path, value: dict[str, Any], target: Path | None) -> None:
    for name, sha256 in value["wheel_sha256"].items():
        if Path(name).name != name or not name.endswith(".whl") or digest(bundle / name) != sha256:
            raise ValueError("wheel filename/hash mismatch")
    subprocess.run(  # noqa: S603 - offline pinned wheel set, no torch/CUDA replacement
        [
            str(python),
            "-I",
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--find-links",
            str(bundle),
            *(["--target", str(target)] if target else []),
            *(value["gpu_dependencies"] if target else value["base_dependencies"]),
        ],
        check=True,
    )


def main() -> None:
    bundle, value = manifest(Path("/kaggle/input"), EXPECTED_MANIFEST_SHA256)
    with (Path("/kaggle/working") / "guard_bootstrap_identity.json").open("x") as stream:
        json.dump(
            {
                "protocol": "guard_pax_bootstrap_v2",
                "bootstrap_commit": BOOTSTRAP_COMMIT,
                "bundle_manifest_sha256": EXPECTED_MANIFEST_SHA256,
            },
            stream,
        )
    with tempfile.TemporaryDirectory(prefix="guard-probe-") as temporary:
        scratch = Path(temporary)
        project, model = scratch / "project", scratch / "model"
        materialize(
            bundle,
            "source.tar.gz",
            value["source_archive_sha256"],
            "pyproject.toml",
            project,
            value["source_sha256"],
            source_commit=value["source_commit"],
        )
        model_hashes = {f["name"]: f["sha256"] for f in value["snapshot"]["files"]}
        materialize(
            bundle,
            "guard-model.tar",
            value["model_archive_sha256"],
            "model.safetensors",
            model,
            model_hashes,
        )
        dependencies = scratch / "dependencies"
        install(Path(sys.executable), bundle, value, dependencies)
        output = Path("/kaggle/working")
        commit = value["source_commit"]
        (output / "guard_bundle_identity.json").write_text(
            json.dumps(
                {
                    "source_commit": commit,
                    "bundle_manifest_sha256": EXPECTED_MANIFEST_SHA256,
                    "snapshot": value["snapshot"],
                    "wheel_sha256": value["wheel_sha256"],
                },
                indent=2,
            )
            + "\n"
        )
        run(
            Path(sys.executable), project, dependencies, commit, "scripts/preflight_clean_worker.py"
        )
        run(
            Path(sys.executable),
            project,
            dependencies,
            commit,
            "scripts/run_clean_v11_dev.py",
            "--output",
            str(output / "dummy"),
        )
        run(
            Path(sys.executable),
            project,
            dependencies,
            commit,
            "scripts/run_clean_v11_dev.py",
            "--output",
            str(output / "dummy"),
            "--resume",
        )
        snapshot_path = scratch / "snapshot.json"
        snapshot_path.write_text(json.dumps(value["snapshot"]))
        run(
            Path(sys.executable),
            project,
            dependencies,
            commit,
            "scripts/probe_phase5_guard.py",
            "--backend",
            "hf",
            "--model-path",
            str(model),
            "--snapshot",
            str(snapshot_path),
            "--output",
            str(output / "guard_probe"),
        )
    print("GUARD_GPU_PROBE_COMPLETE")


if __name__ == "__main__":
    main()
