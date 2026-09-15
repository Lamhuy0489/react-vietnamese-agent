"""Audit the prompt-candidate CPU/native observer outputs without model loading."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_bare_json_probe_v1 import checkpoint
from react_agent.validation.guard_bare_json_audit_v1 import audit_task


def audit_probe(probe: Path, condition: str, source_commit: str) -> dict[str, object]:
    identity = json.loads((probe / "identity.json").read_text())
    if len(source_commit) != 40 or identity.get("source_commit") != source_commit:
        raise ValueError("source commit mismatch")
    tasks = []
    for folder in sorted((probe / "tasks").iterdir()):
        if folder.is_dir():
            tasks.append(
                dict(
                    key=folder.name,
                    checkpoint=checkpoint(folder),
                    audit=audit_task(folder / "execution"),
                )
            )
    return dict(
        protocol="guard_bare_json_probe_v1_cpu_audit",
        valid=True,
        source_commit=source_commit,
        condition=condition,
        tasks=tasks,
        prompt_candidate=True,
        model_inference_runs=0,
        test_payload_accessed=False,
        private_ground_truth_accessed=False,
        phase5_accepted=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--condition", choices=("valid", "trailing_comma", "fenced"), required=True)
    parser.add_argument("--source-commit", required=True)
    # Accepted for launcher parity; candidate audit uses its own bound identity.
    parser.add_argument("--tokenizers", type=Path)
    parser.add_argument("--publishers", type=Path)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.probe, args.output, Path("data")):
        no_links(path)
    if args.output.exists() or args.output.resolve().is_relative_to(args.probe.resolve()):
        raise ValueError("fresh audit destination outside inputs required")
    write_receipt(args.output, audit_probe(args.probe, args.condition, args.source_commit))
    print("BARE_JSON_PROBE_AUDIT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
