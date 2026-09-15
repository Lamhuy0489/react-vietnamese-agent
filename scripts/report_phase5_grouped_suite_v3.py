"""Re-audit and summarize all eight frozen public Dev shards without new inference."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_phase5_grouped_gpu_v3 import audit as audit_shard
from report_phase5_grouped_gpu_v3 import path_coverage, summarize

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.validation.context_stress_audit_v1 import equal
from react_agent.validation.guard_probe_audit_v2 import digest, require

ROOT = Path(__file__).resolve().parents[1]


def combine(pieces: list[dict[str, Any]]) -> dict[str, Any]:
    """Require exact paired coverage and identical full run identities before aggregation."""
    require(len(pieces) == 8, "all eight shards required")
    require(all(type(p["shard"]) is int for p in pieces), "integer shard indices")
    equal(sorted(p["shard"] for p in pieces), list(range(8)), "unique shard indices")
    run = pieces[0]["run"]
    require(
        run["backend"] == "hf"
        and run["expected_tasks"] == 112
        and run["test_payload_accessed"] is False
        and run["quality_scoring"] is False,
        "native public Dev identity required",
    )
    expected = run["tasks"]
    require(len(expected) == len({t["key"] for t in expected}) == 112, "112 unique keys")
    pairs: Counter[tuple[str, str, str]] = Counter(
        (t["pair_id"], t["branch"], t["level"]) for t in expected
    )
    pair_ids = {t["pair_id"] for t in expected}
    equal(len(pair_ids), 8, "eight selected matched pairs")
    require(
        pairs
        == Counter(
            (p, b, f"A{i}") for p in pair_ids for b in ("attack", "benign") for i in range(7)
        ),
        "exact pair/branch/level coverage",
    )
    all_tasks = []
    shard_rows = []
    events: Counter[str] = Counter()
    lifecycle: Counter[str] = Counter()
    classifications: Counter[tuple[str, str, str | None]] = Counter()
    categories: Counter[str] = Counter()
    for piece in sorted(pieces, key=lambda p: p["shard"]):
        equal(piece["run"], run, "full cross-shard run identity")
        tasks = piece["tasks"]
        selected = {t["key"]: t for t in expected if t["shard"] == piece["shard"]}
        require(len(tasks) == len(selected) == 14, "14 tasks per shard")
        equal(sorted(t["key"] for t in tasks), sorted(selected), "exact shard keys")
        for task in tasks:
            equal(task["level"], selected[task["key"]]["level"], "task level binding")
            equal(
                "attack" if task["key"].startswith("ATK_") else "benign",
                selected[task["key"]]["branch"],
                "task branch binding",
            )
        all_tasks.extend(tasks)
        summary = summarize(tasks)
        shard_rows.append(
            dict(
                shard=piece["shard"],
                **{k: v for k, v in summary.items() if k != "tasks"},
                path_coverage=piece["path_coverage"],
            )
        )
        events.update(piece["path_coverage"]["trace_events"])
        lifecycle.update(piece["path_coverage"]["lifecycle"])
        for record in piece["classifications"]:
            classifications[(record["stage"], record["status"], record["error_code"])] += 1
        for task in tasks:
            guard = task["guard_diagnostics"]
            if guard:
                categories.update(r["diagnostic"]["category"] for r in guard["joined"])
    totals = summarize(all_tasks)
    return dict(
        protocol="grouped_gpu_v3_complete_schedule_summary",
        source_commit=run["source_commit"],
        complete_schedule=True,
        expected_tasks=112,
        totals=totals,
        shards=shard_rows,
        levels={
            f"A{i}": summarize([t for t in all_tasks if t["level"] == f"A{i}"]) for i in range(7)
        },
        trace_events=dict(events),
        lifecycle=dict(lifecycle),
        guard_response_categories=dict(categories),
        guard_classifications=[
            dict(stage=k[0], status=k[1], error_code=k[2], count=v)
            for k, v in sorted(classifications.items(), key=lambda x: str(x[0]))
        ],
        phase5_accepted=False,
        quality_scoring=False,
        scope="All frozen native public Dev tasks, failures retained. Runtime completion and "
        "structured validity are not utility/ASR/FPR. Summed per-task wall time is not elapsed "
        "calendar time across concurrent notebooks. No Test/oracle scoring or new inference.",
    )


def inputs(shard: int) -> tuple[Path, Path, Path, Path]:
    """Select only the admitted frozen run, never rejected shard7 aliases."""
    base = ROOT / "results"
    if shard == 0:
        raw = base / "phase5_grouped_v3_s0_download01/raw"
        remote = base / "phase5_grouped_v3_s0_download01/remote"
    else:
        batch = "batch12" if shard < 3 else "batch34" if shard < 5 else "batch56"
        stem = f"phase5_grouped_v3_{'s7' if shard == 7 else batch}"
        raw = base / f"{stem}_download01/raw_s{shard}"
        monitor = "01" if shard < 3 else "02"
        remote = base / f"{stem}_monitor{monitor}/remote_s{shard}"
    manifests = ROOT / "experiments/manifests"
    submission = (
        manifests / f"phase5_grouped_v3_s{shard}_submission{'03' if shard == 7 else '01'}.json"
    )
    selected = manifests / f"phase5_grouped_v3_s{shard}_audit01.json"
    return raw, remote, submission, selected


def collect() -> tuple[list[dict[str, Any]], dict[str, str]]:
    pieces = []
    pins = {}
    preflight = ROOT / "experiments/manifests/phase5_grouped_package_v3_preflight01.json"
    pins[str(preflight.relative_to(ROOT))] = digest(preflight)
    for shard in range(8):
        raw, remote, submission, selected = inputs(shard)
        no_links(selected)
        before = digest(selected)
        result = audit_shard(raw, remote, preflight, submission)
        equal(result, json.loads(selected.read_text()), "independent selected audit reproduction")
        equal(digest(selected), before, "selected receipt immutable")
        pins[str(selected.relative_to(ROOT))] = before
        pins[str(submission.relative_to(ROOT))] = digest(submission)
        identity = json.loads((raw / "grouped/identity.json").read_text())
        equal(identity["shard"], shard, "identity shard")
        classifications = []
        for path in sorted((raw / "grouped/tasks").glob("*/execution/runtime/trace_guard.jsonl")):
            for line in path.read_text().splitlines():
                record = json.loads(line)
                classifications.append(
                    dict(
                        stage=record["stage"],
                        status=record["outcome"]["status"],
                        error_code=record["outcome"]["error_code"],
                    )
                )
        pieces.append(
            dict(
                shard=shard,
                run=identity["run"],
                tasks=result["tasks"],
                path_coverage=path_coverage(raw),
                classifications=classifications,
            )
        )
        equal(inventory(raw), result["raw_sha256"], "raw unchanged during aggregation")
    return pieces, pins


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    require(
        not args.output.exists() and args.output.resolve().parent == ROOT / "results",
        "fresh direct results child required",
    )
    pieces, pins = collect()
    result = combine(pieces)
    for name, value in pins.items():
        equal(digest(ROOT / name), value, "immutable evidence pin")
    result.update(evidence_sha256=pins, script_sha256=digest(Path(__file__)))
    args.output.mkdir()
    write_receipt(args.output / "summary.json", result)
    rows = result["totals"]["tasks"]
    with (args.output / "tasks.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(
        json.dumps(
            dict(tasks=result["totals"]["tasks_count"], terminals=result["totals"]["terminals"])
        )
    )


if __name__ == "__main__":
    main()
