#!/usr/bin/env python3
"""CPU synthetic model-pair rehearsal; explicitly no HF/GPU mode in this version."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.model_pair_probe_v1 import (
    SyntheticPairFactory,
    SyntheticPairObserver,
    run_pair_probe,
)
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    if args.output.exists() or not args.output.resolve().is_relative_to(ROOT / "results"):
        raise ValueError("fresh results-only output required")
    before = prerequisites(ROOT)
    prior_paths = [
        ROOT / "experiments/manifests/phase5_guard_hf_v1_validation01.json",
        ROOT / "experiments/manifests/phase5_agent_loader_v1_validation01.json",
    ]
    count = 0
    for path in prior_paths:
        prior = json.loads(path.read_text())
        for name, expected in prior["source_sha256"].items():
            if sha(ROOT / name) != expected:
                raise ValueError("prior frozen source changed")
            count += 1
    names = [
        "src/react_agent/llm/model_pair_v1.py",
        "src/react_agent/llm/model_pair_probe_v1.py",
        "scripts/probe_phase5_model_pair.py",
        "tests/unit/test_model_pair_v1.py",
        "tests/unit/test_model_pair_probe_v1.py",
        "docs/architecture/phase5_model_pair_v1_contract.md",
    ]
    sources = {name: sha(ROOT / name) for name in names}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603,S607
    clean = not subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)  # noqa: S603,S607
    config = PairConfig(
        ModelIdentity("synthetic-agent", "v1"),
        ModelIdentity("synthetic-guard", "v1"),
        agent_start_seconds=5,
        guard_start_seconds=5,
        agent_call_seconds=2,
        guard_call_seconds=2,
    )
    pair = ModelPair(
        SyntheticPairFactory("agent", args.output),
        SyntheticPairFactory("guard", args.output),
        config,
    )
    result = run_pair_probe(
        args.output,
        pair,
        SyntheticPairObserver(),
        {
            "backend": "synthetic",
            "source_commit": commit,
            "source_sha256": sources,
            "source_worktree_clean": clean,
            "actual_gpu": False,
        },
    )
    if prerequisites(ROOT) != before or any(sha(ROOT / n) != h for n, h in sources.items()):
        raise ValueError("source or seal changed during rehearsal")
    raw = {p.name: sha(p) for p in args.output.iterdir() if p.is_file()}
    write_receipt(
        args.output / "receipt.json",
        {
            "protocol": "model_pair_cpu_rehearsal_v1",
            "valid": result["valid"],
            "source_git_commit": commit,
            "source_worktree_clean": clean,
            "source_sha256": sources,
            "raw_sha256": raw,
            "prior_source_hashes_verified": count,
            "prerequisites": before,
            "summary": result,
            "actual_model_loads": 0,
            "gpu_runs": 0,
            "test_payloads_parsed": 0,
            "phase5_accepted": False,
            "limits": "Real spawn/synthetic inference and simulated memory only; "
            "no actual VRAM claim",
        },
    )
    print(json.dumps(result))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
