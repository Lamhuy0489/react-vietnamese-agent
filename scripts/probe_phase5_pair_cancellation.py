#!/usr/bin/env python3
"""Frozen-source CPU-only rehearsal of three combined pair cancellation cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.model_pair_probe_v1 import SyntheticPairFactory, SyntheticPairObserver
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig
from react_agent.llm.pair_cancellation_v1 import BusyFactory, run_pair_cancellation

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "src/react_agent/llm/pair_cancellation_v1.py",
    "scripts/probe_phase5_pair_cancellation.py",
    "tests/unit/test_pair_cancellation_v1.py",
    "docs/architecture/phase5_pair_cancellation_v1_contract.md",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class StubPairs:
    def __call__(self, trial: str, root: Path) -> ModelPair:
        config = PairConfig(
            ModelIdentity("synthetic-agent", "v1"),
            ModelIdentity("synthetic-guard", "v1"),
            agent_start_seconds=5,
            guard_start_seconds=5,
            agent_call_seconds=0.2,
            guard_call_seconds=0.2,
        )
        return ModelPair(
            BusyFactory(SyntheticPairFactory("agent", root), "agent", trial, root),
            BusyFactory(SyntheticPairFactory("guard", root), "guard", trial, root),
            config,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    if args.output.exists() or not args.output.resolve().is_relative_to(ROOT / "results"):
        raise ValueError("fresh results-only output required")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT):  # noqa: S603,S607
        raise ValueError("commit source before selected CPU rehearsal")
    commit = subprocess.check_output(  # noqa: S603
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True  # noqa: S607
    ).strip()
    before = prerequisites(ROOT)
    prior_count = 0
    for label in ("guard_hf", "agent_loader", "model_pair"):
        pin = json.loads(
            (ROOT / f"experiments/manifests/phase5_{label}_v1_validation01.json").read_text()
        )
        for name, expected in pin["source_sha256"].items():
            if digest(ROOT / name) != expected:
                raise ValueError("prior frozen source changed")
            prior_count += 1
    gpu = json.loads(
        (ROOT / "experiments/manifests/phase5_pair_gpu_v1_preflight02.json").read_text()
    )
    for name, expected in gpu["overlay_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("prior GPU overlay changed")
    source = {name: digest(ROOT / name) for name in SOURCES}
    result = run_pair_cancellation(
        args.output,
        StubPairs(),
        SyntheticPairObserver(),
        {"backend": "stub", "source_commit": commit, "source_sha256": source},
    )
    if prerequisites(ROOT) != before or any(digest(ROOT / n) != h for n, h in source.items()):
        raise ValueError("source or seal changed during rehearsal")
    raw = {
        p.relative_to(args.output).as_posix(): digest(p)
        for p in args.output.rglob("*")
        if p.is_file()
    }
    receipt = {
        "protocol": "pair_cancellation_cpu_rehearsal_v1",
        "source_commit": commit,
        "source_sha256": source,
        "source_worktree_clean": True,
        "prior_source_entries_verified": prior_count,
        "prior_gpu_overlay_verified": 11,
        "prerequisites": before,
        "raw_sha256": raw,
        "summary": result,
        "actual_model_loads": 0,
        "gpu_runs": 0,
        "test_payloads_parsed": 0,
        "phase5_accepted": False,
        "model_memory": "synthetic only",
    }
    write_receipt(args.output / "receipt.json", receipt)
    print(json.dumps(result))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
