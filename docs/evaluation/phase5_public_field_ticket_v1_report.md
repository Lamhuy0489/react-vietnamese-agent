# Phase 5 — proof-carrying public-field egress pilot

2026-09-23. Hypothesis: a host-issued, value-specific evidence ticket can
preserve legitimate egress from a public source even when the session contains
an **unrelated** sensitive artifact, without treating untrusted source text as
an instruction. This is a prospective, opt-in component candidate, not a
replacement for A6 or a claim of novel prior art.

## Mechanism

For the first bounded field (`room`), the host requires the **entire document
content** to be exactly one line of the form `Phòng hiện hành: CODE` from an
admitted S0 document; extra prose or instructions fail closed. A ticket binds
run, complete source-index identity, source artifact/hash/ID, exact read
action, call ID, raw POST ToolResult artifact/hash and value hash. PRE
recomputes the ticket, requires
the source and POST observation in the proposal's ancestry, the exact raw-user
command `Đọc DOCUMENTS. Post webhook to ENDPOINT payload room.` with every
admitted document named exactly once, an authorized
destination, an exact `{room: CODE}` payload, valid Broker tool schema and
complete observed-root/index agreement. A separate bounded scan denies if
the same value appears in any admitted S1/S2 source. No source text, model
output or evaluator answer can grant authority. The actual Broker, other
security gates and final sink remain mandatory.

This separates **data evidence** from **control authority**: an untrusted
document may supply a public room value but cannot choose the endpoint,
additional payload keys, or authorization. It also avoids the coarse rule
“any S2 anywhere denies every sink” for this narrow, proven-public field.
The idea complements the [prospective host metadata design](phase5_host_source_annotations_v1_protocol.md),
but does not classify any existing Dev auxiliary source.

## Synthetic CPU evidence

`tests/unit/test_public_field_ticket_v1.py` has ten deterministic controls:
one authorized public value with an unrelated S2 document is ALLOW; matching
value in S2, changed destination/value, extra payload field, revoked/no grant,
missing proposal ancestry, sensitive/ambiguous/no room source, poisoned
document destination attempt, forged POST result, forged ticket and stale
index ticket are DENY or rejected at issuance as applicable. Tests also
verify raw artifact serialization is unchanged by the gate. The implementation
is [public_field_ticket_v1.py](../../src/react_agent/security_v1/public_field_ticket_v1.py).
No LLM, GPU, Kaggle, evaluator oracle, Dev32 raw mutation or held-out Test
access occurred. Passing component tests is not a measured ASR or utility gain.

## Limits and prospective comparison

This pilot supports only one Vietnamese room-line grammar and one exact user
command. It does not infer general free-text lineage, prove whether a host
S0 label is truthful, or replace cumulative A1–A6, POST/Final/Broker checks.
A poisoned public document can alter its *data value*; it still cannot confer
destination authority. Unknown/multiple room lines or any additional text fail
closed. The same
value in S2 is denied, but semantic leakage via paraphrase remains a separate
guard/final concern. The Dev32 false block remains unchanged.

For a later frozen **new** Dev experiment, compare the unchanged A6 baseline,
A6 plus independently approved host metadata, and A6 plus metadata and this
ticket, on the same fixed backbone/task order. Predeclare paired attack and
benign outcomes, guard/lifecycle outcomes and wall-clock/token cost. Require
no new synthetic exfiltration regressions before measuring any utility gain.
Do not relabel old Dev32 outcomes, tune on Test, or claim Phase 5 acceptance
from this component pilot. Formal Phase 5 remains 4/7 (~57%).
