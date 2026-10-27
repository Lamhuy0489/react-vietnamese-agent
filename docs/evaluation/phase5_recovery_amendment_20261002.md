# Explicit infrastructure amendment — 2026-10-02

Owner approved the acceptance-review implementation. This amendment permits one
exact-request retransmission, not a semantic retry, for the current uncertain
request and other requests on the two specifically reviewed worker bundles.
The frozen native runner, model, prompts, tasks, generation and policy stay
unchanged. The host maintenance script has its own hash and tests; this is an
explicit addition to v2's cached-only recovery procedure, not a silent resume.

Preconditions: original started+uncertain records match the exact payload hash,
task and seven-field worker identity; authenticated READY confirms the same
boot; status is precisely404 REQUEST_UNKNOWN. An immutable claim outside the
original journal records the one-attempt budget before network I/O. A repeated
maintenance command cannot reset it. Successful recovery requires the full
terminal response/hash/durability/quiescence checks used by existing recovery.
Other statuses use cached recovery or remain blocked. Changed boots are refused.

Why a delayed original is safe: the reviewed worker serializes admission under
one lock, keys on request ID plus the entire canonical payload hash, returns
REQUEST_IN_PROGRESS for running duplicates, caches terminal results, never
evicts an admitted ID within the boot, and rejects other instance IDs. Thus two
transmissions of the identical request cannot cause two generations in that
boot.404 alone is not used as proof of completion or definitive non-admission.
No guard cancellation or worker restart is needed for this mechanism.

Current target: b6f50898c6fa4e3a86fbc3cbd2b980a1, C3 webhook/A1. Offline Replay
reconstructed the two earlier request hashes and the exact third payload hash
7737f994b3512601967439b1f98d493f8f03c8d744d51ef32d519c9c154c1d21.
All358 frozen host files matched. Reconstruction is not new model evidence.
Original failed checkpoint remains unchanged even after recovery; the following
68 never-started conditions may resume only after valid journal reconciliation.

Tests exercise the real QuiescentHTTP/QuiescentLifecycle implementation without
network: dropped original, late original, altered payload/boot/task, unreviewed
worker, repeated failure/budget and terminal/cached-only routes. Tests do not
attest real GPU behavior; live terminal attestation is checked separately.

Implementation: scripts/reconcile_phase5_request_v1.py. The specifically reviewed
worker hashes are pinned there. Extension to other implementations is not implicit.
