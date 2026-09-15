# Phase 5 guard observer v2 — synthetic CPU scope

2026-09-15. Opt-in public interfaces, separate from all frozen v1/native factories:

- `llm.guard_diagnostic_backend_v2.DiagnosticFactory(factory, output)` wraps only
  the guard inside its worker. `DiagnosticBackend.generate` returns the identical
  response object and passes through messages/config and transport exceptions.
- `llm.guard_diagnostic_pair_v2.DiagnosticPair(agent_factory, guard_factory,
  config, witness)` extends the existing ShutdownPair, recording hashes of guard
  responses received by the host. No readiness ACK or agent response is recorded.
- `validation.guard_diagnostic_audit_v2.audit(execution, sidecar, witness)` is a
  read-only three-way audit after normal pair/runtime recording has closed.

Worker JSONL protocol `guard_response_sidecar_v2`: contiguous response sequence,
worker PID, request/generation SHA-256, response-identity-match boolean and the
unchanged [structural v2 diagnostic](phase5_guard_diagnostics_v2_contract.md).
Host JSONL protocol `guard_response_witness_v2`: matching response sequence,
host/worker PIDs, actual transport sequence (including readiness offset), request/
generation hashes, response hash/character count and identity-match boolean.
Hashes use SHA-256, response encoding UTF-8 with surrogatepass. The host computes
its hash from received text, never from worker sidecars. No raw text, exception
message, reasoning, prompt contents or unknown schema keys are retained.

Sinks require fresh files in existing directories and one owning process. Missing,
replaced, resized or symlinked append targets fail closed; a failed sink is sticky.
Host sink failure closes/reaps the pair and does not retry model generation.
These observers add I/O and CPU overhead; do not claim timing parity. Agent/
guard model, prompts, generation, parser and security decisions are unchanged
when observer infrastructure works. Semantic failure/retirement remains intact.

Audit requires exact response counts and joins request/generation/PID/sequence
to independently checked runtime attempts and guard traces. Host response hash,
length and identity must equal worker diagnostic identity. Strict JSON models
reject extra fields, duplicate keys and coercions; bounded shape checks validate
size/parser flags, schema issues, syntax offsets/end flags and non-syntax fields.
Errors are sanitized before logging. Runtime files and both sidecars are hashed
and checked for changes across the audit.

Limits: the original runtime has no independent response hash. Consequently v2
needs its host witness; it cannot authenticate historical v1 response hashes.
Without raw text, exact framing/syntax hints cannot be recomputed from hashes.
Consistency is not authenticity against coordinated rewriting of all artifacts,
a compromised process or same-privilege concurrent filesystem attacks. Model
identity booleans are not native weights authentication. Audit returns explicit
`syntax_hints_rederived=false`, `native_model_authenticated=false` and
`guard_quality_validated=false`. Zero responses is not guard-path coverage.

Acceptance: deterministic synthetic CPU tests for unchanged outputs/failures,
actual spawned A2–A6 worker/host joins, PRE/POST retirement, missing/duplicate/
misbound/tampered evidence, strict shape and privacy; setup, Ruff and mypy.
No benchmark Test payloads, oracle, model loading, native wiring, GPU submission
or replay of the 112-task Dev baseline is in this change. Native rollout requires
a separate synthetic protocol, source freeze and isolated package preflight.
