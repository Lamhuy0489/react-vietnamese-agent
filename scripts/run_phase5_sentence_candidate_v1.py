"""CPU-only predeclared comparison; no native dispatch and no benchmark edits."""

from __future__ import annotations

from typing import Any

from prepare_phase5_grouped_package_v3 import dependency_closure as baseline_closure
from run_phase5_acceptance_controls_v1 import main as original_main

from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.runtime_v10 import RUNTIME_VERSION as BASELINE
from react_agent.security_v1.runtime_v11 import RUNTIME_VERSION, SecurityRuntime
from react_agent.validation.acceptance_controls_v1 import run_control as baseline_control


def run_control(*args: Any, **kwargs: Any) -> Any:
    case = args[2]
    return bind(
        baseline_control,
        SecurityRuntime=SecurityRuntime,
        RUNTIME_VERSION=RUNTIME_VERSION if case.level == "A6" else BASELINE,
    )(*args, **kwargs)


def main() -> None:
    def closure(root: Any, entries: Any) -> Any:
        return baseline_closure(
            root, set(entries) | {"scripts/run_phase5_sentence_candidate_v1.py"}
        )

    bind(original_main, run_control=run_control, dependency_closure=closure)()


if __name__ == "__main__":
    main()
