"""Audit retained paired CPU adapter outputs; never start an inference worker."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.validation.final_literal_runtime_audit_v1 import audit_runtime

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-runtimes", type=int, required=True)
    args = parser.parse_args()
    no_links(args.root)
    root = args.root.resolve()
    output = args.output.resolve()
    allowed = ROOT / "build/evaluation"
    if not root.is_dir() or not root.is_relative_to(allowed):
        raise ValueError("local CPU evidence root required")
    if output.exists() or not output.is_relative_to(allowed) or output.is_relative_to(root):
        raise ValueError("fresh separate build/evaluation receipt required")
    paths = sorted(root.glob("**/execution/runtime/final_literal_gate.json"))
    if len(paths) != args.expected_runtimes or args.expected_runtimes < 1:
        raise ValueError("unexpected CPU runtime count")
    rows = [dict(path=p.parent.relative_to(root).as_posix(), **audit_runtime(p.parent))
            for p in paths]
    sources = (
        "src/react_agent/security_v1/final_literal_runtime_v1.py",
        "src/react_agent/security_v1/final_literal_proof_v1.py",
        "src/react_agent/security_v1/value_origin_v4.py",
        "src/react_agent/validation/final_literal_runtime_audit_v1.py",
        "tests/integration/test_final_literal_runtime_v1.py",
        "tests/integration/test_final_literal_room_runtime_v1.py",
        "scripts/audit_phase5_final_literal_runtime_v1.py",
    )
    receipt = dict(
        protocol="phase5_final_literal_runtime_cpu_receipt_v1",
        runtime_count=len(rows), statuses=dict(Counter(row["status"] for row in rows)),
        final_effects=dict(Counter(row["final_effect"] for row in rows
                                   if row["final_effect"] is not None)),
        rows=rows,
        working_tree_sources={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                              for p in sources},
        native_model_runs=0, native_admitted=False, phase5_accepted=False,
        held_out_test_loaded=False, public_field_runtime_enabled=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: receipt[key] for key in (
        "runtime_count", "statuses", "final_effects", "native_admitted"
    )}))


if __name__ == "__main__":
    main()
