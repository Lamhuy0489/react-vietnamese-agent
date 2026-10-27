"""Single Phase 5 integration of existing email and FINAL corrections.

Historical implementations stay intact; all levels use this public runtime.
No notebook changes, new guard prompts or model output representation.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from react_agent.llm.session_journal_v1 import save_new
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.encoded_final_v1 import PROFILE, EncodedFinalGate
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v7 import SecurityRuntime as V7Runtime
from react_agent.security_v1.runtime_v14_email_origin_candidate import (
    SecurityRuntime as EmailRuntime,
)

PROFILE_NAME = "phase5_mainline_integration"


class Phase5Runtime(EmailRuntime):
    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        config = kwargs.get("security_config") or configuration("A0")
        gate = EncodedFinalGate()
        if config.level == "A6":
            parent = SimpleNamespace(_run_task=bind(
                V7Runtime._run_task, release_final_with_entitlement=gate,
                RELEASE_PROFILE=PROFILE))
            run = bind(EmailRuntime._run_task, V7Runtime=parent)
        else:
            run = EmailRuntime._run_task
        result = cast(SecurityRun, run(self, task, **kwargs))
        output = Path(kwargs["output"])
        if config.level == "A6":
            save_new(output / "encoded_final_screen.json",
                     {"profile": PROFILE, "records": gate.records})
        path = output / "run_metadata.json"
        metadata = json.loads(path.read_text())
        metadata["phase5_integration"] = {
            "profile": PROFILE_NAME, "phase5_accepted": False,
            "email_component": "runtime_v14_email_origin_candidate",
            "final_component": PROFILE if config.level == "A6" else None,
            "scope": "synthetic Dev; bounded provenance, not general semantic lineage",
        }
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
        return result
