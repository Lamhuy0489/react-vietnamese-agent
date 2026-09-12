# Phase 5 A4 processing-scope component v1 report

The host-only `a4_processing_scope_v1` component passed 14 deterministic
synthetic conditions. It admits affirmative exact document/cache IDs and
bounded table/column anchors from raw user clauses, keeps state task-local and
monotone, and denies untrusted scope expansion, unassessed search/SQL and
unknown actions. Trusted observations remain pass-through; calculator and
external sinks remain delegated to their existing gates.

The evidence is a component QA receipt, not runtime adoption. No benchmark Dev
or held-out Test payload was parsed, no model was run, and no real side effect
was possible. The component does not implement private-record final
entitlements or prove semantic/casual model influence. Those remain explicit
Phase 5 gates.

See the [component contract](../architecture/phase5_processing_scope_contract.md),
[QA manifest](../../experiments/manifests/phase5_processing_scope_v1_validation01.json)
and [knowledge note](../../knowledge/processing_scope_v1.md).
