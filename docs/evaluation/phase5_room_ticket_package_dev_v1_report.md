# Phase 5 — room-ticket worker package, development preflight v1

2026-09-24 local time. The [builder](../../scripts/prepare_phase5_room_ticket_package_v1.py)
rehearsed the prospective A6 room-ticket adapter in a fresh, offline CPU
environment using the existing frozen clean-worker dependency Dataset and
wheel. This is **working-tree development evidence**, not an admitted Kaggle
release or a native model experiment.

## Scope and result

The worker archive has 172 hash-listed files and includes the room-ticket
adapter, its read-only auditor, inventory admission and their lightweight
policy/schema dependencies. Static closure and an isolated import check exclude
`react_agent.authoring`; unapproved `data/`, private/test/review paths and
traversal are rejected. Splitting the inventory schema and public-field ticket
policies from their host/replay modules removed an incidental authoring import
without changing their public re-exports or the measured v12 runtime.

Both exact source layouts (`source.tar.gz` and expanded `generated/source`)
passed materialization into a new environment with offline wheels, package
origin and tree-hash checks, all eight mock tool schemas/recovery, and 21/21
public clean Dev Dummy tasks. Completed resume did not change checkpoint or
identity hashes; missing-only resume added only the missing task. No held-out
Test or private ground truth was loaded. The local receipt is
`build/kaggle/phase5_room_ticket_dev_preflight01/preflight.json`; its source
manifest is adjacent. Archive SHA-256:
`f3bf9d544a5e7933aa261bf14f7f64c0f117269333a4b1339bb8c714d9f7051c`.
Manifest SHA-256:
`d9e998dba671bad81ddda93f719ebf74768d1f5a0d8339e995c8951bb98d28d5`.
The receipt intentionally says `source_mode=working_tree_cpu_only`,
`source_commit=null`, `selected_prospective_tasks=0`,
`native_inference_runs=0`, `release_admitted=false` and
`phase5_accepted=false`. Git HEAD `3da2e67b2dc007578872dd3247ffefafe40d5f15`
is only the base commit, **not** the source identity of these uncommitted bytes.

QA: 147 focused unit/integration tests passed, including worker-closure
negative controls and compatibility tests for the extracted ticket policies.
`python3 scripts/verify_setup.py`, `ruff check .`, `mypy src scripts`
(518 source files), and `git diff --check` passed. Full pytest was not run
because the repository's authoring tests can open sealed Test material.

## What remains

The archive currently proves import and clean-worker packaging, **not** native
prospective dispatch, selected-pilot content, source authentication, guard
quality, model timing or OS-exit reliability. Before GPU submission, implement
the separately versioned native dispatch and release auditor, pass its fault
and checkpoint tests, freeze one QA'd source commit, create and hash the
`InventoryPin` against that commit **before** authoring synthetic documents,
then bind the exact run/model/environment identities and repeat both layouts.
The [prospective protocol](phase5_room_prospective_v1_protocol.md) and held-out
Test rules remain unchanged; Phase 5 acceptance remains 4/7.
