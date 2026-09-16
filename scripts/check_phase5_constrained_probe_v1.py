"""Exercise constrained probe/resume controls; exact mount rehearsal is a separate gate."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from audit_phase5_constrained_probe_v1 import audit_probe

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.constrained_probe_v1 import SCHEDULE, run
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver
from react_agent.llm.native_constrained_pair_v1 import native_pair


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    no_links(args.output)
    if args.output.exists():
        raise ValueError("fresh CPU evidence directory required")
    args.output.mkdir(parents=True)
    # HF modules import without model libraries; native calls are a later gate.
    if not callable(native_pair) or {"torch", "transformers", "tokenizers"} & sys.modules.keys():
        raise ValueError("lazy native import required")
    project = Path(__file__).resolve().parents[1]
    checks = []
    for condition in ("valid", "backend_failure"):
        root = args.output / condition
        arguments = dict(
            backend="stub",
            commit=args.source_commit,
            observer_factory=SyntheticPairObserver,
            condition=condition,
        )
        environment = project / "data/clean/v1_1/environment"
        result = run(root, environment, **arguments)
        before = inventory(root)
        if run(root, environment, resume=True, **arguments) != result or inventory(root) != before:
            raise ValueError("completed resume mutated evidence")
        first = audit_probe(root, condition, args.source_commit)
        if audit_probe(root, condition, args.source_commit) != first:
            raise ValueError("independent audit differs")
        partial = args.output / (condition + "_partial")
        partial.mkdir()
        shutil.copy2(root / "identity.json", partial / "identity.json")
        for key in SCHEDULE[:-1]:
            shutil.copytree(root / "tasks" / key, partial / "tasks" / key)
        retained = inventory(partial)
        if run(partial, environment, resume=True, **arguments) != result:
            raise ValueError("partial resume result differs")
        after = inventory(partial)
        if any(after.get(name) != sha for name, sha in retained.items()):
            raise ValueError("retained checkpoints changed")
        audit_probe(partial, condition, args.source_commit)
        write_receipt(args.output / (condition + "_audit.json"), first)
        checks.append(
            dict(
                condition=condition,
                tasks=4,
                missing_only_resume=True,
                completed_resume_immutable=True,
                result=result,
            )
        )
    write_receipt(
        args.output / "check.json",
        dict(
            protocol="constrained_probe_v1_cpu_check",
            valid=True,
            checks=checks,
            fresh_task_executions=10,
            copied_terminal_checkpoints=6,
            synthetic_constraint_receipts=True,
            exact_archive_expanded_preflight=False,
            actual_model_loads=0,
            native_model_authenticated=False,
            phase5_accepted=False,
        ),
    )


if __name__ == "__main__":
    main()
