"""Corrected native constraint-root forwarding; preserve the v1 CLI and evidence."""

from run_phase5_clause_dev_native_v1 import main as original_main

from react_agent.llm.clause_dev_dispatch_v2 import run
from react_agent.security_v1.guard_bare_json_v1 import bind


def main() -> None:
    bind(original_main, run=run)()


if __name__ == "__main__":
    main()
