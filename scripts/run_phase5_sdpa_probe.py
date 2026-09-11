#!/usr/bin/env python3
"""Fresh sequential tensor workers; no weights, model mount or benchmark inference."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.sdpa_probe_v1 import cases, run_case
from react_agent.validation.sdpa_probe_audit_v1 import audit_cases


def run(output: Path, backend: str, commit: str) -> dict[str, Any]:
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("committed source required")
    if backend not in ("native", "stub"):
        raise ValueError("explicit backend required")
    no_links(output)
    if output.exists():
        raise ValueError("fresh output required")
    output.mkdir(parents=True)
    write_receipt(
        output / "manifest.json",
        dict(
            protocol="sdpa_tensor_plan_v1",
            source_commit=commit,
            backend=backend,
            cases=cases(),
            process_timeout_seconds=90,
            model_loads=0,
            model_generate_calls=0,
        ),
    )
    for index, case in enumerate(cases()):
        target = output / (case["name"] + ".json")
        if backend == "stub":
            write_receipt(target, run_case(case, backend))
        else:
            subprocess.run(  # noqa: S603 - fixed own entry and predeclared numeric case
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--backend",
                    "native",
                    "--output",
                    str(target.resolve()),
                    "--case",
                    str(index),
                ],
                check=True,
                timeout=90,
            )
    result = audit_cases(output, commit, backend)
    write_receipt(output / "summary.json", result)
    print(
        f"SDPA_TENSOR_COMPLETE native={backend == 'native'} candidate={result['candidate_valid']}"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("stub", "native"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", type=int, choices=range(10))
    args = parser.parse_args()
    if args.case is None:
        run(args.output, args.backend, os.environ.get("PAIR_SOURCE_COMMIT", ""))
    else:
        no_links(args.output)
        if args.backend != "native" or args.output.exists():
            raise ValueError("fresh native child receipt required")
        write_receipt(args.output, run_case(cases()[args.case], "native"))


if __name__ == "__main__":
    main()
