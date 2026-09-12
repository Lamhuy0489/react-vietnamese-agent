# A4 processing-scope component v1

`a4_processing_scope_v1` is a new host-only component, intentionally separate
from frozen `session_policy.py` and runtime v5. It extracts exact affirmative
`DOC_*`/`CACHE_*` IDs and bounded table/column anchors from raw user text. It
rejects negated, conditional, quoted and indirect clauses; it stores the raw
user hash rather than text.

After an untrusted source is observed, a new resource or fan-out search is
denied unless the exact resource or database shape was already observed. An
explicit raw-user anchor is a hard boundary immediately. Calculator and
external sink decisions are delegated to existing gates. Unknown and malformed
scope descriptions fail closed. State is task-local, append-only and
serializable; no ground truth, Test payload, model output or hidden reasoning
is used.

Validation: 14 synthetic conditions, 21 focused unit tests, and the full
repository quality suite are recorded in the [component report](../docs/evaluation/phase5_processing_scope_v1_report.md);
the selected release receipt is created only from a clean source after this
preflight.
This is not runtime integration, private-final entitlement, ASR/utility or
Phase 5 acceptance. Next is a new versioned runtime composition and differential
audit, followed by private-final policy and grouped Dev/freeze work.
