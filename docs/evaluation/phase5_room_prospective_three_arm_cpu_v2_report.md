# Phase 5 — prospective three-arm CPU gate v2

2026-09-24 local time. The prospective room experiment now has separately
named `baseline`, `metadata` and `ticket` A6 routes using the same synthetic
task, environment and ExitPair/guard transport. The baseline and metadata
controls invoke the existing v12 constrained runtime without changing its
policy; baseline passes no new source catalog, metadata passes only the
owner-reviewed S0/S2 catalog, and ticket uses the separately versioned v15
adapter. Each route checks the same approved inventory pin before a worker
starts. This is an ablation, **not** a change to the measured Dev32 runtime.

The [v2 manifest](../../src/react_agent/validation/room_prospective_run_manifest_v2.py)
extends the ticket-only v1 schema to three arms with a common comparison ID.
An independent read-only triplet audit requires all fields except `arm` to
match exactly; a one-arm seed change is rejected. The
[v2 launcher](../../scripts/run_phase5_room_prospective_native_v2.py) uses
the same external run SHA, committed source, task/environment, model,
generation and output-overlap admission for all arms. The two v12 controls have
a [native dispatcher](../../src/react_agent/llm/room_control_native_dispatch_v1.py)
and [independent release auditor](../../src/react_agent/validation/room_control_native_release_v1.py)
with immutable raw checkpoint, read-only completed resume, and no automatic
retry of partial/errors. A joined v12 pair must be valid before a checkpoint
is sealed. The ticket arm keeps its own runtime and auditor.

On the same scripted CPU clean-room specimen, baseline without metadata denied
all three proposed tools (including both document reads), metadata allowed
the two reads but denied the webhook, and ticket allowed the authorized mock
webhook. These are observable branch differences, **not** model-utility or
benchmark ASR/FPR estimates. Negative controls reject a wrong pin before pair
startup, mismatched arm/seed across manifests, changed task/run identity,
tampered raw artifacts and partial resume.

The final development package receipt is
`build/kaggle/phase5_room_ticket_dev_preflight08/preflight.json`. Both archive
and expanded mounts pass in fresh offline environments: 186 hash-listed
worker files, eight mock tools/recovery, 21/21 public clean Dummy tasks per
layout, completed and missing-only resume. Archive SHA-256:
`f4f6f921cfdc785196a4bc9d67b048b7d8b418fa4e9d57b48b733a5750b1c3e4`.
Source-manifest SHA-256:
`c8ac33881b4cde77901d91374e5349638153c3ebf9af12468c68de46795bacb7`.
The receipt is working-tree CPU only: `source_commit=null`,
`selected_prospective_tasks=0`, `native_inference_runs=0`, and
`release_admitted=false`.

QA: 163 focused tests passed; setup, Ruff, mypy (528 source files) and diff
check passed. Full pytest was not run because authoring tests can open sealed
Test material. No production inventory pin, prospective document content,
committed package, Kaggle submission, model-quality/timing result, remote
publisher authentication or Phase 5 acceptance is claimed. Formal acceptance
remains 4/7. The next gate is one selective source freeze excluding personal
reports/figures, followed by committed exact-package QA; only then create
the inventory pin **before** writing synthetic pilot documents.
