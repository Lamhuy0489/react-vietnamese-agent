"""Freeze a complete public worker and exercise both mount layouts in fresh offline venvs."""

from __future__ import annotations

import argparse
import ast
import base64
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

from prepare_phase5_document_probe import BASE, WHEEL_SHA, committed_sources, digest, load

from react_agent.foundation.dev_validation import prerequisites

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = "notebooks/kaggle/grouped_native_kernel_v3.py"
BUILDER = "scripts/prepare_phase5_grouped_package_v3.py"
BUNDLE_SHA = "b14976413b72898b6c0c1b8c46c1ebb0f62f63633f647ab2064fbc048262240f"
ENTRYPOINTS = {
    "scripts/run_phase5_grouped_dev.py",
    "scripts/audit_phase5_grouped_dev.py",
    "scripts/check_phase5_grouped_package_v3.py",
    "scripts/collect_phase5_tokenizer_metadata.py",
    "scripts/preflight_clean_worker.py",
    "scripts/run_clean_v11_dev.py",
}
PUBLIC = {
    "data/adversarial/release_v2/dev_attack.jsonl",
    "data/adversarial/release_v2/dev_benign.jsonl",
    "data/adversarial/release_v2/seal.json",
    "docs/evaluation/qwen7b_upstream_inventory_v1.json",
    "docs/evaluation/publisher_policy_v1/agent_generation_config.json",
    "docs/evaluation/publisher_policy_v1/guard_generation_config.json",
}
# The original worker deliberately uses this namespace without its development
# __init__, which imports pool QA. Do not introduce that evaluator dependency.
OMIT = {"src/react_agent/validation/__init__.py"}


def dependency_closure(root: Path, seeds: set[str]) -> set[str]:
    """Follow static Python imports including lazy native imports and package parents."""
    pending, result = set(seeds), set()

    def module_file(module: str) -> str | None:
        stem = "src/" + module.replace(".", "/")
        for name in (stem + ".py", stem + "/__init__.py"):
            if name not in OMIT and (root / name).is_file():
                return name
        return None

    while pending:
        name = pending.pop()
        if name in result or name in OMIT:
            continue
        result.add(name)
        if not name.endswith(".py"):
            continue
        path = root / name
        for parent in Path(name).parents:
            init = (parent / "__init__.py").as_posix()
            if init not in OMIT and (root / init).is_file():
                pending.add(init)
        parts = Path(name).with_suffix("").parts
        package = list(parts[1:-1]) if parts[0] == "src" else []
        for node in ast.walk(ast.parse(path.read_text())):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                prefix = package[: len(package) - node.level + 1] if node.level else []
                stem = ".".join(prefix + ([node.module] if node.module else []))
                modules = [stem] + [stem + "." + a.name for a in node.names]
            for module in modules:
                found = module_file(module)
                if found:
                    pending.add(found)
                elif "." not in module and (root / "scripts" / (module + ".py")).is_file():
                    pending.add("scripts/" + module + ".py")
    return result


def make_archive(root: Path, files: dict[str, str], target: Path) -> None:
    base = load(ROOT / BASE)
    with (
        target.open("xb") as output,
        gzip.GzipFile(fileobj=output, mode="wb", mtime=0, filename="") as zipped,
    ):
        with tarfile.open(fileobj=zipped, mode="w", format=tarfile.USTAR_FORMAT) as archive:
            for name, expected in sorted(files.items()):
                base.relative_name(name)
                if digest(root / name) != expected:
                    raise ValueError("source changed while archiving")
                data = (root / name).read_bytes()
                item = tarfile.TarInfo(name)
                item.size, item.mode = len(data), 0o644
                archive.addfile(item, io.BytesIO(data))


def file_hashes(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob("*")) if p.is_file()
    }


def rehearse(
    wrapper: ModuleType,
    dataset: Path,
    value: dict[str, Any],
    wheel: Path,
    layout: str,
    evidence: Path,
) -> dict[str, Any]:
    evidence.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="grouped-exact-") as temporary:
        scratch = Path(temporary).resolve()
        base = wrapper.bootstrap(scratch)
        archive = scratch / "source.tar.gz"
        wrapper.source_archive(archive)
        mount = scratch / "input/dataset"
        mount.mkdir(parents=True)
        if layout == "archive":
            shutil.copy2(archive, mount / "source.tar.gz")
        elif layout == "expanded":
            base.extract(archive, mount / "generated/source", wrapper.SOURCE_FILES)
        else:
            raise ValueError("known layout required")
        project = scratch / "project"
        base.materialize(
            mount,
            "source.tar.gz",
            wrapper.ARCHIVE_SHA,
            "pyproject.toml",
            project,
            wrapper.SOURCE_FILES,
            source_commit=wrapper.SOURCE_COMMIT,
        )
        isolated = scratch / "venv"
        subprocess.run(  # noqa: S603 - fixed local interpreter/fresh venv
            [str(Path(sys.base_prefix) / "bin/python3"), "-I", "-m", "venv", str(isolated)],
            check=True,
        )
        python = isolated / "bin/python"
        base.install(python, dataset, value, None)
        subprocess.run(  # noqa: S603 - pinned offline wheel
            [str(python), "-I", "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)],
            check=True,
        )

        def run(*args: str) -> None:
            base.run(python, project, None, wrapper.SOURCE_COMMIT, *args)

        run("scripts/preflight_clean_worker.py")
        dummy, partial = evidence / "dummy", evidence / "partial"
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy))
        before = file_hashes(dummy / "tasks")
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy), "--resume")
        if len(list((dummy / "tasks").iterdir())) != 21 or before != file_hashes(dummy / "tasks"):
            raise ValueError("clean completed resume altered tasks")
        partial.mkdir()
        shutil.copy2(dummy / "identity.json", partial / "identity.json")
        for task in sorted((dummy / "tasks").iterdir())[:-1]:
            shutil.copytree(task, partial / "tasks" / task.name)
        retained = file_hashes(partial)
        run("scripts/run_clean_v11_dev.py", "--output", str(partial), "--resume")
        after = file_hashes(partial)
        if len(list((partial / "tasks").iterdir())) != 21 or any(
            after.get(n) != h for n, h in retained.items()
        ):
            raise ValueError("clean missing-only resume changed retained work")
        run("scripts/audit_phase5_grouped_dev.py", "--help")
        run(
            "scripts/check_phase5_grouped_package_v3.py",
            "--source-commit",
            wrapper.SOURCE_COMMIT,
            "--output",
            str(evidence / "grouped"),
        )
        base.verify_tree(project, wrapper.SOURCE_FILES)
        return dict(
            layout=layout,
            valid=True,
            clean_tasks=21,
            tool_schemas=8,
            missing_only_resume=True,
            grouped=json.loads((evidence / "grouped/package_check.json").read_text()),
            raw_sha256=file_hashes(evidence),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle output required")
    output.mkdir(parents=True)
    before = prerequisites(ROOT)
    commit = subprocess.check_output(  # noqa: S603,S607 - fixed read-only Git query
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True  # noqa: S607
    ).strip()  # noqa: S607
    dataset = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset"
    if digest(dataset / "guard_bundle.json") != BUNDLE_SHA:
        raise ValueError("immutable Dataset manifest mismatch")
    value = json.loads((dataset / "guard_bundle.json").read_text())
    for name, expected in value["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("base source changed: " + name)
    names = dependency_closure(ROOT, set(value["source_sha256"]) | ENTRYPOINTS) | PUBLIC
    base = load(ROOT / BASE)
    allowed_data = {n for n in value["source_sha256"] if n.startswith("data/")} | PUBLIC
    for name in names:
        base.relative_name(name)
        if name.startswith("data/") and name not in allowed_data:
            raise ValueError("unapproved worker data")
    files = committed_sources(names, commit)
    source = committed_sources(
        names
        | {
            BASE,
            TEMPLATE,
            BUILDER,
            "scripts/prepare_phase5_document_probe.py",
            "docs/architecture/phase5_grouped_package_v3_contract.md",
        },
        commit,
    )
    wheel = ROOT / "build/kaggle/worker_progress_v1_wheels/tqdm-4.67.3-py3-none-any.whl"
    if digest(wheel) != WHEEL_SHA:
        raise ValueError("exact progress wheel required")
    archive = output / "source.tar.gz"
    make_archive(ROOT, files, archive)
    kernel_pins = []
    for shard in range(8):
        code = (ROOT / TEMPLATE).read_text()
        substitutions = {
            "__SOURCE_COMMIT__": commit,
            "__BASE_SOURCE__": base64.b64encode((ROOT / BASE).read_bytes()).decode(),
            "__BASE_SHA__": source[BASE],
            "__ARCHIVE__": base64.b64encode(archive.read_bytes()).decode(),
            "__ARCHIVE_SHA__": digest(archive),
            "__BUNDLE_SHA__": BUNDLE_SHA,
            "{}  # __SOURCE_FILES__": repr(files),
            "0  # __SHARD__": str(shard),
        }
        for key, replacement in substitutions.items():
            if code.count(key) != 1:
                raise ValueError("unique template placeholder required")
            code = code.replace(key, replacement)
        kernel = output / f"kernel_s{shard}"
        kernel.mkdir()
        worker = kernel / "grouped_native_kernel_v3.py"
        worker.write_text(code)
        metadata = json.loads((dataset.parent / "kernel/kernel-metadata.json").read_text())
        metadata.update(
            id=f"huylmhuhu/react-vn-grouped-dev-v3-s{shard}",
            title=f"ReAct VN Grouped Dev v3 shard {shard}",
            code_file=worker.name,
            model_sources=["qwen-lm/qwen2.5/transformers/7b-instruct/1"],
            dataset_sources=[value["dataset"]],
            kernel_sources=[],
            competition_sources=[],
            enable_gpu=True,
            enable_tpu=False,
            enable_internet=False,
            is_private=True,
            machine_shape="NvidiaTeslaT4",
            docker_image_pinning_type="original",
            docker_image="gcr.io/kaggle-private-byod/python@sha256:"
            "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        )
        (kernel / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        kernel_pins.append(
            dict(shard=shard, requested_id=metadata["id"], files=file_hashes(kernel))
        )
    wrapper = load(output / "kernel_s0/grouped_native_kernel_v3.py")
    os.environ["PAIR_SOURCE_COMMIT"] = commit
    checks = [
        rehearse(wrapper, dataset, value, wheel, layout, output / "cpu" / layout)
        for layout in ("archive", "expanded")
    ]
    if source != committed_sources(set(source), commit) or prerequisites(ROOT) != before:
        raise ValueError("source or seals changed during rehearsal")
    receipt = dict(
        protocol="grouped_package_v3_preflight",
        valid=True,
        source_commit=commit,
        source_sha256=source,
        package_sha256=files,
        archive_sha256=digest(archive),
        bundle_manifest_sha256=BUNDLE_SHA,
        tqdm_wheel_sha256=WHEEL_SHA,
        checks=checks,
        kernels=kernel_pins,
        prerequisites=before,
        actual_model_loads=0,
        gpu_runs=0,
        test_payload_accessed=False,
        phase5_accepted=False,
        package_rehearsal_passed=True,
        native_submission_ready=False,
        remaining=[
            "full source QA",
            "live owner/mount/quota check",
            "GitHub source push",
            "native runs and artifact audit",
        ],
        scope="Public-only packaged CPU evidence, not native quality or release acceptance",
    )
    (output / "preflight_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("GROUPED_PACKAGE_V3_PREFLIGHT_OK", flush=True)


if __name__ == "__main__":
    main()
