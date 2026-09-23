# Phase 5 — new content-free synthetic room inventory and paired CPU control

2026-09-23. This is a **development-only synthetic pair**, not a relabel of
Dev32, an approved public-Dev inventory, or a model experiment. The declared
[inventory](../../experiments/manifests/phase5_room_synthetic_inventory_v1.json)
contains only source IDs, types, sensitivity and trust—no document payload,
oracle or attack label. Its file SHA-256 is
`c0854a8775c2ca35103e4dbef2b4cb3c4ace3740d8497e088df3e5e5cb4ab77c`.
Status remains `assistant_draft_unreviewed`. No `InventoryPin` with a real
source commit/review reference has been issued.

The two new IDs were not in the earlier `AUX_ROOM`/`AUX_PRIVATE` pilot:
`AUX_NEWROOM` is S0/UNTRUSTED; `AUX_NEWPRIVATE` is S2/UNTRUSTED. The manifest is
loaded and hash-checked before each temporary environment is materialized.
[`SyntheticRoomInventory`](../../src/react_agent/validation/synthetic_room_inventory_v1.py)
requires the exact sorted source IDs and rejects missing, extra or duplicate
auxiliary documents. It constructs the host catalog from IDs/labels alone;
changing either clean or poisoned document text cannot change it. Tests also
reject a trust promotion and a Python `model_copy` status bypass. This
establishes local construction order, not historical independent human review.

The new
[paired integration](../../tests/integration/test_prospective_room_inventory_v1.py)
uses the same task, scripted agent responses and catalog across branches. The
room value `ROOM8421` appears as one complete line in the clean public source.
The v12 baseline denies the webhook after an unrelated S2 read; v13 admits it
through Broker and still reaches POST/Final. An appended instruction in the
public document is denied; so is a branch where `ROOM8421` also occurs in the
S2 source. The candidate metadata continues to say
`host_inventory_attested=false` and `synthetic_cpu_candidate_only`. These are
deterministic Replay controls, not measured benign utility or attack success.

During development an initial draft reused the historical pilot IDs; it was
replaced with fresh IDs **before** the final paired test and source freeze.
That draft is not prospective evidence and no result from it is selected as an
experiment. The prior pilot tests remain unchanged. No released Dev/Test
fixture, evaluator oracle, model prompt, frozen raw artifact or production A6
runtime was modified. The code and manifest are still uncommitted local work;
the file hash is a CPU regression pin, not an authenticated Git release.

The exact-line room grammar remains deliberately narrow. Before model use,
the owner must independently review a genuinely new public source inventory
before ingestion, preserve the record, pin it with a source commit in a run
manifest, then complete broader grammar/typed-origin paired controls and a
separate native runtime/package identity. The guard lifecycle issue and Phase 5
formal 4/7 (~57%) status are unchanged.

A separate [review request](phase5_room_inventory_review_request_v1.md)
predeclares **different, unused IDs** for a possible future pilot without
creating their payloads. It awaits an explicit owner label decision; the CPU
inventory above cannot be promoted retroactively into that role.

Local QA: 107 related unit/integration tests passed, including unchanged v12
and earlier ticket controls; setup verification, repository-wide Ruff, mypy on
509 source files, knowledge-check and diff-check passed. Full pytest was not
run because sealed Test authoring tests are outside this active-phase scope.
