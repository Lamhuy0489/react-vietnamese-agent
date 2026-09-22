# Phase5 — compound authorization and cumulative CPU validation

2026-09-21. **78/78 declared synthetic controls pass; six Dev destination gaps
are resolved at parser level. Phase5 is not complete.**

[Contract](../architecture/phase5_clause_authorization_v3_contract.md),
[control receipt](../../experiments/manifests/phase5_clause_candidate01.json),
[public Dev coverage](../../experiments/manifests/phase5_clause_coverage01.json),
[credential scan](../../experiments/manifests/phase5_clause_scan01.json).

## Changes and measured results

The v11 candidate supported read-then-send punctuation only at A6. V12 adds
raw-clause destination extraction across A1–A6, conservative quotation/conditional/
revocation handling, and preserves raw A0. A named-resource prohibition does not
revoke a different public payload's destination; it never grants sensitive egress.

During integration, a separate defect was reproduced: an email followed by a
sentence-final period was missing from the old origin index even after its
destination grant was recognized. The new host-only supplemental index binds
that literal to the original user artifact, retaining labels and hashes. Unknown
payload, sensitive-source, guard/rule veto and final leakage controls still pass.

| Fixed synthetic form | Expected behavior observed |
|---|---:|
| Semicolon read/send | 26/26 |
| Sentence read/send | 26/26 |
| Sentence read/send + named-resource prohibition | 26/26 |

The separate public-Dev check retains the prior 16 fixtures/8 paired families;
the six requested destinations now parse, versus zero of six in the baseline.
The remaining ten fixtures grant no email/webhook destination. Neither this count
nor the synthetic control pass rate is a model utility, ASR or FPR estimate.
Source labels are unchanged, including CONFIDENTIAL linked sources: some requested
Dev payloads can still legitimately be denied by sensitivity/value policy.

Raw: `results/phase5_clause_candidate01`; selected audit preparation:
`results/phase5_clause_selected01`. Independently rechecked 157 execution-source
pins, 1,400 raw hashes and 78 unique control identities; actual tool sequences,
denial counts, raw instruction identities and final effects agree with receipts.
Credential-value scan: 1,401 files, zero matches. No model/GPU inference.

## Verification and remaining gates

New targeted checks: 67 parser/origin/component tests and 65 runtime integration
tests pass. The integration checks include A0 prompt/action/final parity and
guard traces at A2–A6; they are bounded synthetic checks, not exhaustive parity.
[Expanded QA](../../experiments/manifests/phase5_clause_qa01.json):
873 focused unit/regression tests pass (60.91s), 351 integration tests pass
(310.06s); setup, Ruff, mypy (478 source files), knowledge and diff checks pass.
182 frozen native-source pins, all 10 prior acceptance-QA source pins and 169
tracked data hashes are unchanged. Full repository pytest was deliberately not
run: sealed Test-authoring fixtures remain excluded. Logs are preserved in
`results/phase5_clause_qa01` with hashes in the QA receipt.

Git base `6d039e255a0a0a91f6e514cfebe889c4b7ae8aed`; the receipts bind the
**uncommitted working tree**, not a new GitHub release. Old measured source and
outputs are not replaced. No Test payload or private ground truth was parsed;
only public Dev instructions and synthetic controls informed this change.

Next: constrained ExitPair/native integration and independent audit identities,
then exact package preflight and the predeclared 32-task A2/A6 workload. Native
quality/utility, lifecycle reliability and final DoD freeze remain open. No new
Kaggle submission or routine commit; formal acceptance stays 4/7 groups (~57%).
