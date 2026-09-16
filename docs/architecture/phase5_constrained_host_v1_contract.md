# Phase 5 constrained host/runtime integration v1

2026-09-16. New opt-in modules only; preserve frozen runtime, worker and source
pins. Reuse bare-JSON prompt, strict parser, guard generation 128/greedy/seed42,
pair lifecycle and policy bodies. No benchmark/Test/private GT or GPU run here.

The host role adapter validates the exact native constrained factory topology,
model identity and task-owned pair before startup. After a guard response it
requires the four complete constraint receipts and joins PID, request index,
request/generation/response hashes, decoding identity, ordered processors,
callback/output counts and restoration. Missing/changed evidence fails closed;
no repair/retry. Each task has a fresh classifier and decoding-bound cache.

Before a cache hit, verify host ownership, unchanged pair configuration/factories,
resident worker health and unchanged validated receipt history. This is **not a
remote introspection of live model configuration**: the worker validates that
configuration around every actual generation. No new hidden IPC/inference request
is added to claim a cache check. Source-authenticated exclusive worker ownership
is required for adoption; synthetic tests do not prove native behavior.

Runtime uses the unchanged A2–A6 policy loop via private function bindings. Its
version and metadata explicitly name the constrained execution/cache identity.
Audit reuses existing pair/gate/sidecar/host-witness validators, with only the
cache-key encoding extended by protocol and decoding identity. It never rewrites
saved traces. Complete constraint records must join every successful response;
failed/incomplete requests remain recorded and must not be counted as completion.

Acceptance for this step: synthetic success/cache reuse, identity/receipt drift,
worker error/interrupt, ownership and baseline isolation tests; spawned CPU pair
through A2/A6 and read-only audit. Native policy/attention/metrics release joins,
exact package and source-authenticated GPU protocol remain separate gates.
