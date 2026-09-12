# A4 processing-scope component v1

This is a bounded, host-only A4 component milestone. It adds a deterministic
resource boundary without modifying the frozen A3–A5 session policy or the
current v5 runtime. It does not read benchmark ground truth, evaluator grants,
held-out Test payloads or model-produced authorization claims.

## Boundary and identity

`ProcessingScope` is created once per task from the raw user instruction. The
raw text is represented only by a SHA-256 identity in the component snapshot.
The component accepts exact synthetic `DOC_*` and `CACHE_*` resource IDs, and
explicit `table`/`bảng` and `column`/`cột` identifiers from affirmative clauses.
Negated, conditional, quoted or indirect clauses are not authorization. Anchor
matching is exact for resource IDs and case-folded for SQL identifiers. A hard
anchor count and raw-user byte budget prevent unbounded state.

The component never infers authorization from a source value, destination,
evaluator sidecar or a model declaration. It records only opaque source and
artifact identities supplied by the host. Sensitivity is intentionally absent:
the existing A3/A5 session and A6 value gates remain the authority for that
dimension.

## Action assessment

Only non-executing descriptions are produced:

- `doc_read` and `cached_fetch` carry one exact resource ID;
- `db_query` accepts only one small `SELECT column[, ...] FROM table` shape;
- search actions are always considered unassessed because they can fan out;
- calculator and external sinks are delegated to their existing gates;
- unknown actions fail closed.

SQL is parsed with a bounded regular grammar. Semicolons, comments, wildcard,
subqueries, expressions and aliases are unassessed; no SQL is executed here.

## A4 decision rule

When disabled, decisions are pass-through. When enabled, an explicit raw-user
scope is a hard boundary from the first action. Without an explicit anchor,
the first read is allowed until a host observation marked `UNTRUSTED` is seen;
after that point, an action may revisit only a previously observed exact
resource or previously observed database table/column subset. Any new resource,
search, malformed query or unsupported shape returns `DENY` with observable
`UNTRUSTED_CONTROL_INFLUENCE` and action/unknown-field reason codes. External
destination/payload authorization is explicitly delegated to the existing A4
and A6 gates, so this component cannot accidentally weaken them.

State is append-only and task-local: untrusted state, observed artifact IDs,
resource IDs and database shapes never clear or downgrade. A failed source-ID
integrity check is atomic and leaves the prior snapshot unchanged. The snapshot
and identity are suitable for a later runtime audit, but are not model input.

## Evidence and limits

The v1 QA covers exact document/cache anchors, table/column scope, untrusted
scope expansion, search and malformed-SQL fail-closed behavior, trusted
pass-through, delegated sinks, unknown actions, state serialization and bounds.
It is synthetic component evidence only. It does not yet compose the component
into a new runtime, establish complete Vietnamese intent parsing, prove causal
LLM influence, authorize private final records, or provide ASR/utility/model
metrics. A future runtime version must preserve the frozen v5 source and add
independent differential/parity evidence before this component can contribute
to Phase 5 acceptance.
