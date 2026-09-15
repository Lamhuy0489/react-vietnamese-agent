"""Candidate prompt bindings for unchanged transport and worker-host witness audits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, RUNTIME_VERSION, bind
from react_agent.validation.guard_diagnostic_audit_v2 import audit as original_join
from react_agent.validation.pair_runtime_audit_v3 import audit_task as original_task


def audit_task(output: Path) -> dict[str, Any]:
    result = cast(dict[str, Any], bind(original_task, PROMPT=PROMPT)(output))
    if result["runtime_present"]:
        metadata = json.loads((output / "runtime/run_metadata.json").read_text())
        if metadata["runtime_version"] != RUNTIME_VERSION:
            raise ValueError("candidate runtime version mismatch")
        if metadata["guard_prompt_hash"] != text_hash(PROMPT):
            raise ValueError("candidate prompt metadata mismatch")
    return result


def audit_join(execution: Path, sidecar: Path, witness: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any], bind(original_join, audit_task=audit_task)(execution, sidecar, witness)
    )
