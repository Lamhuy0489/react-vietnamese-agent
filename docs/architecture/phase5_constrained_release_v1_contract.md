# Constrained GPU release authentication v1

2026-09-17. This is a host-side, read-only release wrapper around the frozen
constrained native auditor. It does not change the worker, source freeze
`0d4e82f`, prompt, decoding, model, policy or shutdown deadline.

## Before submission

`scripts/audit_phase5_constrained_gpu_v1.py:validate_package` verifies the selected
committed preflight against its original full receipt, 172 local/Git source pins,
166 archive members, exact kernel inventory, private/offline/GPU settings and
literal embedded source/archive/bootstrap/Dataset hashes. No downloaded Python
is executed. The known hash-pinned CPython311 launcher cache is a local rehearsal
artifact only; remote source evidence must contain just source and metadata.

Do not recreate an existing notebook or retry terminal semantic failures.
Check actual account, accelerator quota and private Dataset readiness/version;
confirm the pinned model mount via platform metadata after submission. The
notebook/source is already committed and pushed; host audit additions do not
require another worker source freeze.

## Submission and download records

Submission receipt binds the selected preflight hash, source commit, actual
handle, numeric kernel ID/version, private flag, notebook URL, actual remote
source hash and Dataset handle/version. IDs/versions must be positive integers,
not booleans. The guard Dataset version is frozen at 1.

Observation is collected from Kaggle before output download and again afterward:
`before_download` and top-level fields must bind the same actual handle, numeric
ID/version, private flag, source hash and COMPLETE status. Record inventories
`raw_sha256` and `remote_sha256` only after download. ERROR/CANCELLED artifacts
must still be preserved, but cannot pass this COMPLETE-only release wrapper;
diagnosis or recovery would require a separately documented path, not a retry.

These records are trusted collection evidence, not cryptographic statements
signed by Kaggle. Synthetic tests cannot establish remote availability or native
execution. Live platform calls, pinned source pull and before/after version checks
are required for actual release evidence; inventory agreement alone is not enough.

## Read-only release audit

Verify remote settings/mounts, executable hash, bootstrap protocol/source mode/
archive/Dataset/snapshot/wheel pins. Run the existing constrained native auditor
independently and require exact agreement with the worker's saved report.
Raw and remote inventories must be unchanged afterward. Reject duplicate JSON
keys, symlinks, traversal, duplicate/nonregular archive members, and stale identities.
CLI output must be fresh under `results/` and outside all supplied inputs.

`source_authenticated=true` is a wrapper result only after these gates pass.
The nested native report retains its narrower claims. Neither package readiness
nor artifact integrity establishes guard quality, benign utility, graceful
lifecycle or Phase 5 acceptance. Do not open held-out Test/private ground truth.
