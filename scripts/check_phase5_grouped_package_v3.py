"""Execute public grouped stub shards and audit origins/checkpoints inside the package."""

import argparse
import json
import sys
from pathlib import Path

from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.grouped_dev_identity_v2 import identity
from react_agent.llm.grouped_dev_runner_v2 import run
from react_agent.validation.grouped_dev_checkpoint_v2 import audit_prefix


def module_origins(root: Path) -> dict[str, str]:
    """Fail closed on editable-install leakage, including namespace package paths."""
    origins = {}
    source = (root / "src").resolve()
    for name, module in sys.modules.copy().items():
        if name != "react_agent" and not name.startswith("react_agent."):
            continue
        filename = getattr(module, "__file__", None)
        paths = [filename] if filename else list(getattr(module, "__path__", []))
        if not paths or any(not Path(p).resolve().is_relative_to(source) for p in paths):
            raise ValueError("development import leaked into worker: " + name)
        origins[name] = Path(paths[0]).resolve().relative_to(root).as_posix()
    if {"torch", "transformers", "tokenizers"} & sys.modules.keys():
        raise ValueError("stub rehearsal loaded native libraries")
    return origins


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if sys.prefix == sys.base_prefix:
        raise ValueError("fresh rehearsal venv required")
    module_origins(root)
    release, environment = (
        root / "data/adversarial/release_v2",
        root / "data/clean/v1_1/environment",
    )
    manifest, _ = identity(release, environment, args.source_commit, "stub")
    args.output.mkdir(parents=True, exist_ok=False)
    keys: list[str] = []
    for shard in range(8):
        path = args.output / f"shard_{shard}"
        params = dict(commit=args.source_commit, shard=shard)
        run(path, release, environment, max_new_tasks=1, **params)
        first = inventory(path / "tasks")
        run(path, release, environment, resume=True, **params)
        after = inventory(path / "tasks")
        if any(after.get(k) != h for k, h in first.items()):
            raise ValueError("missing-only resume changed retained task")
        before = inventory(path)
        run(path, release, environment, resume=True, **params)
        checks = audit_prefix(path, manifest, shard)
        if len(checks) != 14 or inventory(path) != before:
            raise ValueError("incomplete or mutable shard")
        keys.extend(c["key"] for c in checks)
        print(f"GROUPED_PACKAGE_SHARD_OK {shard} tasks=14", flush=True)
    if len(keys) != len(set(keys)) or set(keys) != {t["key"] for t in manifest["tasks"]}:
        raise ValueError("112 unique scheduled keys required")
    report = dict(
        valid=True, origins=module_origins(root), keys=keys, shards=8, actual_model_loads=0
    )
    (args.output / "package_check.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
