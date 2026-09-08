# Phase 5 guard acquisition and synthetic GPU probe v1

Scope: technical preflight, not final guard selection, benchmark tuning, ASR or
Phase 5 acceptance. Existing guard HF adapter/runtime/policies remain immutable.

## Acquisition

The official HF API at the already declared 40-character revision supplies file
sizes, Git blob SHA-1 for ordinary files and LFS SHA-256 for weights. The checked-in
`configs/guard_hf_v1/qwen_1_5b_upstream.json` records those publisher values before
download. The acquisition script constructs HTTPS URLs from that typed allowlist;
TLS verification stays enabled. An explicit CA bundle may fix local CA setup.
It never reads Kaggle/HF tokens or downloads an unpinned revision.

Ten files including license must match sizes and publisher hashes; ordinary files
use Git's `blob <size>\0` prefix, not plain-file SHA-1. All local files also receive
SHA-256. Snapshot identity then uses the frozen adapter's descriptor. Failed
downloads keep partial bytes and a class-only failure receipt, no automatic retry.
This trusts publisher metadata over authenticated HTTPS, not a signed attestation.
Weights may be acquired before source freeze, but committed packaging independently
rechecks every byte before inference. Weights stay ignored under `build/`.

## Declared probe

Two independent trials, always in this order:

1. One warm worker receives complete synthetic inputs A, B, A.
2. A new worker receives A once after the first worker has closed/reaped.

Use direct `WarmGuardBackend.generate`, bypassing ModelGuard's classification
cache. Greedy 128 tokens, seed 42, existing guard prompt/parser; full first-request
deadline 120 seconds includes CUDA operation, snapshot hash scans and model load.
HF trial factory requires two T4 GPUs, tests an actual tensor operation inside
the guard child on device 1, then loads the frozen single-device adapter. No
CUDA/model is initialized in the parent merely to pass preflight.

Backend/JSON failure retires that trial, remaining calls are recorded skipped.
The separately predeclared fresh-A trial is not a retry of an earlier failed
answer. No JSON repair, prompt alteration, alternate model or semantic retry.
Each trial persists attempts/lifecycle and complete structured outcomes after
cleanup; the run manifest is written before execution. Store only hashes of raw
responses, valid guard JSON and metrics, never arbitrary invalid/hidden reasoning.

Technical `valid` requires four schema-valid responses and exact raw-response
hash equality for all three A calls. This is a small deterministic-state probe,
not proof that every possible HF state/history is absent. Stub-valid is solely
transport QA; the stub does not measure detection quality. GPU timings retain
cold load, warm calls and process-local allocation peaks; free-memory endpoints
are not concurrent global peaks. No agent model is resident in this probe.

## Packaging and release gates

Only a committed source allowlist, frozen public clean Dev environment/selection,
weights, license and hash-pinned wheels enter the private worker Dataset. No Test,
private GT, pools, reviews, credentials or project memory. Kernel embeds the exact
manifest hash. Source/model archives require exact inventory, no links/traversal/
duplicate members; expanded directories must match the same inventories.

Both layouts execute inside a new local venv built from the base Python, with
offline pinned dependencies, frozen `src` in PYTHONPATH, no user site, no inherited
development venv imports or bytecode writes. Verify all eight tools/fault recovery,
21 Dummy tasks, completed-checkpoint resume, and a new partial-checkpoint copy
with 20 retained/one missing task. Completed artifacts must remain byte-identical.
Run the four-call stub probe in each exact layout. Real GPU packages reuse eight
hash-verified inference wheels from the measured pilot plus newly pinned base
wheels for Mac cp311/Linux cp311/cp312; do not replace Kaggle's torch/CUDA stack.

GPU bootstrap installs dependencies and materializes source/model under temporary
directories, not exportable `/kaggle/working`. Keep only diagnostic Dummy outputs,
probe receipts and bundle identity in working output. Private Dataset/kernel,
source push, exact bundle receipt, chosen-account quota and Dataset version/readiness
must be verified before kernel submission. Preserve failed artifacts and separate
infrastructure errors from invalid/model responses; never retry semantic failures.

Next: real probe/cancellation evidence, versioned agent placement and combined
memory stress, then grouped Dev protocol/quality and remaining Phase 5 acceptance.
