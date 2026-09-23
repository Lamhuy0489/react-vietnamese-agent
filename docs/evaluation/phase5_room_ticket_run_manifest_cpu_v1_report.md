# Phase 5 — prospective room-ticket run manifest and launcher, CPU QA v1

2026-09-24 local time. The separately versioned
[run-manifest validator](../../src/react_agent/validation/room_ticket_run_manifest_v1.py)
and [native launcher](../../scripts/run_phase5_room_ticket_native_v1.py)
now require an **externally supplied run-manifest SHA-256** before any model
worker starts. This closes the gap between a source-admitted single-task
dispatcher and a reproducible prospective ticket-arm invocation; it does not
start the owner-approved pilot.

The strict manifest predeclares one A6 `ticket` task/condition, source commit
and manifest hash, reviewed draft and review byte hashes, both canonical and
file-byte `InventoryPin` hashes, task/environment byte identities, immutable
agent inventory/model revision, guard snapshot/revision, runtime/generation
config bytes, seed and evaluator version. Admission reads observed environment
document IDs and refuses a mismatched S0/S2 inventory. The launcher's output
must not overlap any frozen input. `--admit-only` checks these pins without
loading model weights, while execution requires GPU preflight and delegates to
the task checkpoint/release-audit gate. The external manifest SHA is also in
the task identity, so a completed resume under another manifest is rejected.

Negative CPU controls reject an altered external SHA, reformatted pin file,
changed environment bytes, changed seed/config bytes, source drift, wrong pin,
output/input overlap and mismatched resume identity. No pilot payload, source
freeze, Kaggle submission or real HF inference occurred. This launcher covers
the **ticket arm only**; baseline and metadata arms from the
[prospective protocol](phase5_room_prospective_v1_protocol.md) still require
equivalent pinned launchers and paired analysis. One-task manifests do not
estimate benchmark ASR/FPR, and source tree equality does not authenticate a
remote notebook or model publisher.

QA: 157 focused tests passed; setup, Ruff, mypy (522 source files) and diff
check passed. Development package
`build/kaggle/phase5_room_ticket_dev_preflight06/preflight.json` passed archive
and expanded mounts in fresh offline environments with 180 worker files,
eight mock tools/recovery, 21/21 clean Dev Dummy tasks per layout and safe
resume. Archive SHA-256:
`b676b3c8f9d2da0f58ca192244b1dfa4e45f9e22677cf165b07507cd4b4a795c`.
Source-manifest SHA-256:
`394944e7477dbcc59ae141acd7cc7f3ab0b63a2ae46a72b6ae89b8d8ccb53021`.
The receipt remains `source_commit=null`, `native_inference_runs=0`,
`release_admitted=false`. Full pytest was not run because authoring tests can
open sealed Test material. Formal Phase 5 acceptance stays 4/7.

Next: implement the same frozen admission for the baseline/metadata arms,
then freeze one coherent source commit and repeat exact package QA in committed
mode. Only after the real source commit exists may the team create the
production `InventoryPin`, author synthetic pilot documents, freeze the run
manifest and consider Kaggle native execution with publisher/remote audits.
