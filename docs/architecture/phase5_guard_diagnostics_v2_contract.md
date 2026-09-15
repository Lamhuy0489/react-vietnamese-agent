# Phase 5 structural guard diagnostics v2 — CPU component

2026-09-15. Public function `diagnose(text: str) -> GuardDiagnosticV2` in
`react_agent.security_v1.guard_diagnostics_v2` is opt-in, not connected to any
native factory or runtime policy. It supplements immutable v1 diagnostics without
changing the authoritative parser, prompt, generation or classifier outcome.

Output contains the unchanged v1 diagnostic plus fixed framing/syntax enums,
a terminal-fence boolean and optional bounded character offset/end-of-input/
trailing-comma indicators. Parser-error messages are mapped to allowlisted enums;
unknown wording maps to `other`. No raw text, error message, validation input,
unknown key, field value, decoded payload or hidden reasoning is emitted.

Framing describes only the first non-whitespace token, not valid JSON. Offset
is a Python string character index, not a byte offset. End-of-input errors do
not prove token-budget truncation. No wrapper stripping, repair, coercion or
fallback acceptance occurs. Inputs above65536characters retain v1 size/hash
identity but skip extra inspection; depth rejection preserves v1 behavior.
Hashing still traverses the input, so the length check is not a bound on hashing
cost. Diagnostics are not security decisions or a policy input.

71 focused synthetic checks cover v1/v2 classifications, errors, determinism,
privacy, parser non-repair, bounded size/depth, old observer and trace joins.
This is CPU-only evidence; no native v2 sidecar/worker joining or GPU experiment
is implemented. Existing v1 worker/source pins and the112-run baseline remain
immutable. Historical raw guard text was not retained: v2 cannot retroactively
diagnose which exact syntax defect caused those30 responses.

Next: a separately versioned observer sidecar and independent auditor, with
request/PID/sequence/response identity and JSON-shape consistency validation.
Test deterministic CPU process/trace joins and adversarial sidecar mutations,
then define a new synthetic native diagnostic protocol before packaging. No
automatic prompt/parser repair or rerun of the existing Dev failures.
