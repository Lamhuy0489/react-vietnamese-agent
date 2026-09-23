# Phase 5 — room-ticket native gate, CPU wiring evidence v1

2026-09-24 local time. A separately versioned
[native dispatcher](../../src/react_agent/llm/room_ticket_native_dispatch_v1.py)
now connects the approved prospective A6 room-ticket route to the existing
lazy ExitPair model factory. A separate
[read-only release auditor](../../src/react_agent/validation/room_ticket_native_release_v1.py)
checks an externally pinned committed source manifest, exact public worker
tree, task identity, immutable raw hashes, paired guard/exit join, runtime
source commit and inventory pin. Neither component changes the historical v12
runtime, Dev32 outputs or held-out Test.

The native gate rejects a working-tree manifest, changed source bytes,
missing worker code, authoring code, an incorrect inventory pin and output
overlap before a model worker starts. It requires explicit A6 via the pinned
runtime, creates a per-task identity and checkpoint, closes the pair on run
failure, and permits `resume=True` only for a completed, re-audited
checkpoint. Partial/error output remains in place for manual infrastructure
triage; it is never retried automatically. A failed pair join leaves no
checkpoint. CPU tests also confirm that a changed task identity or mutated raw
artifact invalidates a completed resume.

The gate was exercised with fake model factories for wiring/fault tests, **not
with pretrained weights**. The earlier paired Replay controls still provide
the behavioral evidence for clean/poison/S2/wrong-destination/final-leak
conditions. The isolated [package builder](../../scripts/prepare_phase5_room_ticket_package_v1.py)
now imports both native modules. Final development rehearsal
`build/kaggle/phase5_room_ticket_dev_preflight04/preflight.json` passed both
archive and expanded source layouts in new offline virtual environments:
178 hash-listed worker files, eight mock tools/recovery, 21/21 clean Dev Dummy
tasks per layout, and completed/missing-only resume. Its archive SHA-256 is
`b8dc1be97540d313d82a266e2dba215ce21ee3fbb1b7822b3c28b16647637702`;
source-manifest SHA-256 is
`1de946357b33bdf3bd48b78a8f12ad779a318d202d8155eafb1b14c3b44b0bcb`.
The receipt explicitly has `source_commit=null`, zero prospective/native
runs, and `release_admitted=false`.

QA: 154 focused unit/integration tests passed; repository setup, Ruff and
mypy (520 source files) passed. The full suite was not run because authoring
tests can open sealed Test material. No Kaggle submission, GPU inference,
model-publisher authentication, independent human attestation, pilot document
content, production `InventoryPin`, committed package or Phase 5 acceptance
claim follows from this work. Formal acceptance remains 4/7.

Next: add a frozen prospective launcher/manifest binding external source,
model, generation and environment pins; complete committed source/package QA;
create the `InventoryPin` against that source commit **before** synthetic
document authoring; then run the declared paired controls/native pilot and
audit model quality, timing and lifecycle without tuning on Test.
