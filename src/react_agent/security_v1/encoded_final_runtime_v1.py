"""Opt-in FINAL-only correction; public runtime/guard lifecycle and PRE/POST preserved."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from react_agent.llm.session_journal_v1 import save_new
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.encoded_final_v1 import PROFILE, EncodedFinalGate
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.remote_api_runtime_v1 import RemoteAPIRuntime
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v7 import SecurityRuntime as V7Runtime
from react_agent.security_v1.runtime_v12 import SecurityRuntime as V12Runtime


class EncodedFinalRuntime(RemoteAPIRuntime):
    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        config = kwargs.get("security_config") or configuration("A0")
        if config.level != "A6":
            return super()._run_task(task, **kwargs)
        gate = EncodedFinalGate()
        parent = SimpleNamespace(_run_task=bind(V7Runtime._run_task,
            release_final_with_entitlement=gate, RELEASE_PROFILE=PROFILE))
        result = cast(SecurityRun, bind(V12Runtime._run_task, V7Runtime=parent,
            RUNTIME_VERSION="security_runtime_encoded_final_v1")(self, task, **kwargs))
        save_new(Path(kwargs["output"]) / "encoded_final_screen.json",
                 {"profile": PROFILE, "records": gate.records,
                  "scope": "FINAL only; PRE/POST/index/grants unchanged"})
        return result
