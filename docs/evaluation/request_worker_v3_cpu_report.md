# Request worker v3 — CPU integration and isolated package QA

2026-09-28. Implemented a versioned HF stop-event/synchronization adapter,
quiescence-aware lifecycle, bounded HTTP server, worker composition and host
terminal-status verifier. [Contract](../architecture/request_worker_v3_contract.md).
Frozen v1/v2 files and earlier native outputs remain unchanged. No Test/private
oracle was read; no model inference or notebook submission occurred in this work.

The native loader reuses the original HF engine rather than changing prompts or
decoding. It connects per-request cancellation and synchronizes both devices
after generation. Failure or uncertain cleanup retires the instance; successful
cancellation cannot be recorded merely because cancellation was requested.
CPU tests use explicitly synthetic engines and CUDA substitutes.

Focused controls cover delayed cleanup and busy admission; cancellation during
cleanup; fresh stop events; failed synchronization on either device; sanitized
generation errors; interrupts; output/cache bounds; disk failure at terminal
commit; HTTP authentication before reading/lookup; boot/hash mismatches;
malformed payloads; concurrent status/cancel and duplicate delivery; connection
limits and slot release; and immutable host reconciliation receipts. A resolved
execution status explicitly does not authorize semantic retry.

Exact package preflight passes4/4role-layout cases: agent/guard across archive
and generated expanded directory layouts. All8modules are imported from the
package with isolated Python `-I -S` (no site-packages/editable development
imports). Auth, cancellation ordering, duplicate suppression, fresh next
request and journal privacy pass. No runtime tools, benchmark inputs, ground
truth or credentials are included in the8-file inference-only bundle.

Raw: `build/evaluation/request_worker_v3/preflight01`, including exact source,
archive, probe and receipt. Builder:
[`preflight_request_worker_v3.py`](../../scripts/preflight_request_worker_v3.py).
The source is a working-tree candidate, not a committed/pushed deployment freeze.

Remaining deployment work is explicit in the contract: actual host transport/
journal integration, notebook entrypoint/discovery/lifetime shutdown, final
source freeze and native GPU diagnostic. Current notebooks need no modification
for the existing runtime. This candidate is not deployed and does not close
Phase5, native cancellation or long-lived model VRAM/lifecycle acceptance.

Verification:103focused/regression tests pass in37.02s; setup, Ruff and mypy
(590source files) pass. This includes prior v2 lifecycle/HTTP, v1 journal,
paired scoring and public-runtime/Dev/provenance regressions. Full suite was not
repeated: its two historical frozen-pin failures remain documented in handoff.
[CPU receipt](../../experiments/manifests/request_worker_v3_cpu01.json) binds
candidate source, tests, report and package evidence. No Phase5 gate promoted.
