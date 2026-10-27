"""Identify the Phase 5 closure candidate without promoting its evidence.

The wrapper preserves the constituent runtime and candidate metadata. A common
entrypoint is useful for tracing the experiment, but does not establish A0
parity, configuration isolation, or native admission by changing a label.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.phase5_runtime import Phase5Runtime as IntegratedRuntime
from react_agent.security_v1.runtime import SecurityRun

RUNTIME_FAMILY = "phase5_v14_closure_v1"
RUNTIME_VERSION = "security_runtime_phase5_v14_closure_v1"
ADMISSION_PROFILE = "phase5_closure_cpu_controls_v1"


class Phase5ClosureRuntime(IntegratedRuntime):
    """Single closure runtime class used for A0 through A6."""

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        result = super()._run_task(task, **kwargs)
        output = Path(kwargs["output"])
        metadata_path = output / "run_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        level = (kwargs.get("security_config") or configuration("A0")).level
        metadata["phase5_closure"] = {
            "runtime_family": RUNTIME_FAMILY,
            "runtime_version": RUNTIME_VERSION,
            "admission_profile": ADMISSION_PROFILE,
            "security_level": level,
            "scope": "synthetic Dev bounded closure controls",
            "evidence_status": "candidate_not_accepted",
            "implementation_runtime_version": metadata["runtime_version"],
        }
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return result
