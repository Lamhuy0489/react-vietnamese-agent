# Phase5 acceptance coverage and authorization candidate — 2026-09-21

Phase5 remains4/7 acceptance groups. This work identifies and locally addresses
a bounded benign-utility defect; it does not close guard quality or native reliability.
[Contract](../architecture/phase5_acceptance_controls_v1_contract.md).

## Public Dev coverage

[Matrix](../../experiments/manifests/phase5_acceptance_coverage01.json) retains the
eight families previously selected by the frozen grouped Dev seed, both branches,
16public fixtures. Proposed A2/A6 workload:32tasks, dispatch disabled. No model
outputs were used in selection; no benchmark data or held-out Test was changed.
The matrix never enters runtime policy or prompts.

| Family | Required behavior | DoD focus |
|---|---|---|
| LINKMAIL | Public email after reading an unrelated protected artifact | 5/9/13/14/15 |
| SOURCEBINDING | Current-source webhook, not stale cached value | 5/9/13/15 |
| DATABASE | Permitted SQL column, no secret column disclosure | 5/14/15/16 |
| ENCODED | Protected-code egress/final handling | 5/13/14 |
| LINKPAGE | Read only named document/page | 5/15/16 |
| QUERYLEAK | Public search query after protected read | 5/13/14/15 |
| QUOTED | Treat quoted instructions as data; no unsolicited email | 5/14/15 |
| ROWLIST | Authorized row only | 5/14/15/16 |

All three externally addressed families (six paired fixtures) have no recognized
v1 destination anchor. Their instructions combine reading with sending, or a
permitted send with a later prohibition. This is a measured parser-coverage gap,
not proof that the payload ought to be sent: ENCODED sensitive egress is still
forbidden even if its destination is recognized. No native run was launched.

## Frozen baseline versus opt-in candidate

Use26declared synthetic controls, each with read authorization followed by either
a semicolon or a period. Public source labels and scripted guard verdicts are
explicit. Include both mock sinks, S0/S1/S2 and trust combinations, unrelated
secret/A5 contrast, unknown origin, wrong destination, rule/guard/error vetoes,
and protected final-answer cases. Socket use is prohibited by integration tests.

| Current runtime/form | Expectations met | Unmet |
|---|---:|---:|
| v10, semicolon | 26/26 | 0 |
| v10, period | 17/26 | 9 |
| v11 candidate, semicolon | 26/26 | 0 |
| v11 candidate, period | 26/26 | 0 |

[Baseline](../../experiments/manifests/phase5_acceptance_baseline01.json),
[candidate](../../experiments/manifests/phase5_acceptance_candidate01.json).
The nine baseline failures are retained, not re-labelled as passing acceptance.
The initial integration test uncovered the same nine failures; final regression
tests explicitly distinguish expected baseline limitations from candidate success.
The candidate is a different source identity, not a retry for improved model scores.

`authorization_anchors_v2.py` adds only explicit, unquoted read-then-send sentence
forms. It preserves original grants, binds the original user-text hash, and refuses
new grants for blocks containing quotes, negation or conditionals. It does not
normalize source/tool text into authority. `runtime_v11.py` applies this opt-in
candidate consistently at the A6 coarse-anchor and value-origin gates, retaining
all other vetoes. A0–A5 delegate to v10; this is **not yet an accepted cumulative
A0–A6 rollout**. Frozen v1 rules/v10/native workers and past results remain unchanged.

New parser tests cover positive forms and quotation, negation, conditional,
reported/example instructions, email/URL boundaries and legacy-grant parity.
The candidate is deliberately incomplete: compound instructions with later
prohibitions remain conservatively rejected. The six Dev anchor gaps are not
claimed fixed by these synthetic successes. No native model quality measured.
The read-directive detector is lexical, not a formal parse of resource references.
Before promotion, add read-prefixed reported prose (for example, a request to read
an unquoted instruction) and cross-clause quote/revocation controls. Passing this
bounded suite must not be interpreted as general natural-language authorization.

## Evidence and next concrete work

Raw: `results/phase5_acceptance_controls01` and `results/phase5_sentence_candidate01`.
52executions each;933raw files per run, plus summaries. Source closures, inputs,
saved metadata/tool dispatch/final effects and selected receipts independently
checked. [Credential scan](../../experiments/manifests/phase5_acceptance_scan01.json):
1,868files, zero known credential values. Raw remains local/untracked.

Final [QA](../../experiments/manifests/phase5_acceptance_qa01.json):806focused
unit/regression tests passed in52.98s;286integration tests passed in256.06s.
Setup, Ruff, mypy474, knowledge links and diff checks passed. All182native package
source pins and prior QA pins remain unchanged. The full repository pytest suite
was not run because held-out Test-authoring fixtures remain excluded. These are
software regression counts, not an acceptance percentage or native quality score.

Next: define clause-scoped positive/negative authorization with immutable raw
spans and explicit quote context; tests must prove a later prohibition cannot
grant or silently revoke the wrong action. Resolve the declared public Dev anchor
gaps without weakening sensitive-egress policy; validate cumulative levels/A0
parity and native pair integration before a fresh package/source freeze. Then
run the declared paired coverage workload, retain every denial/error and measure
guard decisions separately from agent utility. Lifecycle reliability and20DoD
formal freeze remain open. No commit/push/GPU submission in this work.
