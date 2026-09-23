"""Launch one externally pinned prospective A6 ticket task, or admission-only QA.

The read-only admission path never loads model weights. Actual HF execution
requires a committed exact source package and GPU preflight.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.llm.model_pair_hf_v1 import verify_gpu_environment
from react_agent.llm.room_ticket_native_dispatch_v1 import run
from react_agent.validation.room_ticket_run_manifest_v1 import admit_output, admit_run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-manifest", required=True, type=Path)
    parser.add_argument("--run-sha256", required=True)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--draft", required=True, type=Path)
    parser.add_argument("--pin", required=True, type=Path)
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--environment", required=True, type=Path)
    parser.add_argument("--model-inventory", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--runtime-config", required=True, type=Path)
    parser.add_argument("--generation", required=True, type=Path)
    parser.add_argument("--agent", required=True, type=Path)
    parser.add_argument("--guard", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--admit-only", action="store_true")
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    admit_output(
        args.output,
        (
            project,
            args.run_manifest,
            args.source_manifest,
            args.review,
            args.draft,
            args.pin,
            args.task,
            args.environment,
            args.model_inventory,
            args.snapshot,
            args.runtime_config,
            args.generation,
            args.agent,
            args.guard,
        ),
    )
    manifest, task, review, draft, pin, snapshot, runtime, generation = admit_run(
        args.run_manifest,
        args.run_sha256,
        project=project,
        source_manifest=args.source_manifest,
        review_path=args.review,
        draft_path=args.draft,
        pin_path=args.pin,
        task_path=args.task,
        environment=args.environment,
        model_inventory=args.model_inventory,
        snapshot_path=args.snapshot,
        runtime_config_path=args.runtime_config,
        generation_path=args.generation,
    )
    if args.admit_only:
        if args.resume:
            raise ValueError("admit-only does not resume or inspect prior task output")
        print(
            json.dumps(
                {
                    "protocol": manifest.protocol,
                    "admitted": True,
                    "task_id": task.task_id,
                    "native_model_loaded": False,
                    "source_authenticated_by_remote_audit": False,
                }
            ),
            flush=True,
        )
        return
    verify_gpu_environment()
    result = run(
        task,
        output=args.output,
        project=project,
        source_manifest=args.source_manifest,
        expected_source_sha256=manifest.source_manifest_sha256,
        source_commit=manifest.source_commit,
        environment=args.environment,
        review=review,
        draft_bytes=draft,
        pin=pin,
        expected_pin_sha256=manifest.inventory_pin_sha256,
        run_manifest_sha256=args.run_sha256,
        agent=args.agent,
        model_inventory=args.model_inventory,
        guard=args.guard,
        snapshot=snapshot,
        runtime_config=runtime,
        generation=generation,
        resume=args.resume,
    )
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
