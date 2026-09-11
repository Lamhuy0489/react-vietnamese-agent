#!/usr/bin/env python3
"""Real daemon-spawn readiness rehearsal with native-shaped objects, no weights."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from react_agent.llm.agent_hf_v2 import AgentHFBackendV2
from react_agent.llm.agent_mount_v1 import MODEL, no_links, write_receipt
from react_agent.llm.base import LLMBackend
from react_agent.llm.efficient_stress_v1 import instrument_pair
from react_agent.llm.generation_policy_v1 import PolicyStressFactory
from react_agent.llm.guard_hf_v1 import GuardHFBackend, GuardHFConfig
from react_agent.llm.guard_snapshot_v1 import CANDIDATE_REVISION, MODEL_ID
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig, Role
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory

GUARD_REVISION = (
    f"hf:{CANDIDATE_REVISION};snapshot-sha256:"
    + "36b6d38e9e3cbc47427b1fabcf6f44fdd926a1d95a04a33bbfb19d7f1ffd5fbe"
)


@dataclass(frozen=True)
class NativeShapeFactory:
    role: Role
    evidence: Path

    def __call__(self) -> LLMBackend:
        # Bypass model constructors deliberately. Only factory admission and
        # readiness are exercised; never call model.generate on these objects.
        value: Any = object.__new__(AgentHFBackendV2 if self.role == "agent" else GuardHFBackend)
        value.model_id = MODEL if self.role == "agent" else MODEL_ID
        value.model_revision = AGENT_REVISION if self.role == "agent" else GUARD_REVISION
        if isinstance(value, GuardHFBackend):
            value.config = GuardHFConfig()
        write_receipt(
            self.evidence,
            {
                "pid": os.getpid(),
                "role": self.role,
                "native_shaped_placeholder": True,
                "actual_model_loads": 0,
            },
        )
        return cast(LLMBackend, value)


def run(root: Path) -> None:
    no_links(root)
    root.mkdir(parents=True, exist_ok=False)
    rows = []
    for corrected in (False, True):
        trial = root / ("corrected" if corrected else "original_failure")
        trial.mkdir()
        output, policy = trial / "probe", trial / "policy"
        pair = ModelPair(
            NativeShapeFactory("agent", trial / "agent_shape.json"),
            NativeShapeFactory("guard", trial / "guard_shape.json"),
            PairConfig(
                ModelIdentity(MODEL, AGENT_REVISION),
                ModelIdentity(MODEL_ID, GUARD_REVISION),
                agent_start_seconds=10,
                guard_start_seconds=10,
            ),
        )
        if corrected:
            instrument_pair(pair, output, policy, trial / "attention")
        else:
            # Preserve the actual v1 topology as a positive failure control.
            for role in ("agent", "guard"):
                worker = pair._workers[role]
                worker.factory = ThreadProgressFactory(
                    PolicyStressFactory(
                        worker.factory, role, output / f"{role}_stress", policy / role
                    )
                )
        error = None
        try:
            pair.start()
        except RuntimeError:
            error = "RuntimeError"
        finally:
            pair.close()
        snapshot = pair.snapshot()
        write_receipt(trial / "closed.json", snapshot)
        workers = snapshot["workers"]
        if any(w["handle_pending"] for w in workers.values()):
            raise ValueError("factory rehearsal left a worker")
        expected = ["OK", "OK"] if corrected else ["BACKEND_FAILURE"]
        statuses = [a["status"] for r in ("agent", "guard") for a in workers[r]["attempts"]]
        if statuses != expected or (error is None) != corrected:
            raise ValueError("factory-order control outcome differs")
        if list(trial.rglob("entered.json")) or list(trial.rglob("completed.json")):
            raise ValueError("readiness consumed single-use stress backend")
        rows.append(
            {
                "corrected": corrected,
                "statuses": statuses,
                "error": error,
                "native_model_calls": 0,
                "weights_loaded": 0,
                "all_handles_reaped": True,
                "stress_call_not_consumed": True,
            }
        )
    write_receipt(
        root / "summary.json",
        {
            "protocol": "efficient_factory_shape_rehearsal_v1",
            "valid": True,
            "phase5_accepted": False,
            "native_context_verified": False,
            "rows": rows,
            "scope": "Actual spawn/progress/factory/readiness only; model constructors bypassed",
        },
    )
    print(
        "EFFICIENT_FACTORY_SHAPE_COMPLETE original=BACKEND_FAILURE corrected=READY native_calls=0"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
