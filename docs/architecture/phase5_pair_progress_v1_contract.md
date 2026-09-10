# Pair progress v1 — predeclared GPU prevention validation

Scope: a new private/offline `huylmhuhu/react-vn-pair-progress-v1` kernel, not a
replacement version or semantic retry of prior IPC/cancellation results.
Keep all 15 IPC overlay files and the frozen Dataset v1 unchanged; add only
`worker_progress_v1.py` and `run_phase5_pair_progress_worker.py` to that overlay.
Keep image digest, Qwen 7B/1.5B revisions, placement, caps, deadlines, three
cancellation trials and zero-generation protocol unchanged. No local weights
acquisition, Test/private GT payload, model-quality tuning or phase transition.

## Worker ordering and evidence

Lazy `TracedFactory(ProgressReceiptFactory(original_factory))`: child tracing
starts before `configure_worker_progress`, which precedes native HF imports.
The unchanged native policy pins tqdm 4.67.3/std.py hash and installs a
threading.RLock only in an untouched daemon spawn worker. A durable policy
receipt binds PID, role and the actual configuration return before loading.
Outer tracing records dependency identities and factory success/failure.
An owner receipt binds this distinct protocol/source and lifecycle owner PID.

The original IPC manifest identity remains unchanged in shape, with a new Git
source commit. Separate progress identity and six policy files explicitly bind
the treatment; the read-only auditor requires them. Do not infer treatment from
absence of warnings, or reuse an old IPC run as treated data.

## Exact preflight

Rehearse archive and expanded/PAX Dataset layouts in isolated venvs, frozen
source PYTHONPATH only, all eight tools/fault adapter, 21 public Dummy tasks,
completed resume and missing-only resume with 20 checkpoints preserved.
Run all three cancellation trials with synthetic backends but **native tqdm**;
all six workers must bind policy receipts and show zero tracked registrations;
the parent's 90 transport registrations must balance.

CPU preflight installs only the independently downloaded pure-Python wheel
`tqdm-4.67.3-py3-none-any.whl`, SHA256
`ee1e4c0e59148062281c49d80b25b67771a127c85fc9676d3be5f243206826bf`;
verify its std.py bytes against the GPU-observed pin before offline install.
It is not added to the frozen Dataset or uploaded: the GPU image's native
package must independently satisfy the same exact version/source check.
Untracked user reports are allowed outside the payload. Tracked worktree/index
must be clean and every overlay/template/builder file committed. Do not stage
the user's reports to satisfy a blanket clean-tree check.

## Measured acceptance and limits

Audit unchanged HF-load identities, six worker PIDs and forced/graceful exits,
all eighteen VRAM recovery samples, parent transport and child trace ledgers,
six policy receipts, owner PID binding, exact remote source/private metadata,
raw inventory and seals. New output inventory is 106 files (99 IPC-equivalent
plus seven progress identity/policy files). Preserve raw bytes and warnings.

Integrity-valid and prevention-pass are separate fields. Prevention passes only
with zero observed child registrations, parent 90/90 balanced, no unmatched
entries and no shutdown semaphore warnings. Nonzero entries remain measured
misses, not an excuse for automatic reruns. Zero does not prove complete IPC/OS
cleanup, native generation cancellation or graceful shutdown. Forced exits must
remain reported. Instrumented timings cannot be pooled with historical runs.

Require exact preflight and full QA, committed/pushed source and receipt, then
current account/quota/private Dataset readiness checks before one submission.
Download to a fresh directory and audit twice without inference. Context stress,
runtime integration, A4/final entitlement scope and grouped Dev freeze remain
separate Phase 5 gates, even if this diagnostic passes.
