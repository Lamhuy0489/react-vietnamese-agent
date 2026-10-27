# Phase 5 — embedded-identifier Dev matrix result, 2026-09-24

## Decision

**Do not integrate v4 into A6 runtime as-is.** On the predeclared 18-case
synthetic Dev matrix, v4 protects all six in-profile embedded private literals
but suppresses all three legitimate user/public echoes when the same literal
also appears in S1/S2. The mechanism is useful; the final-release utility
tradeoff does not pass the [declared gate](phase5_embedded_identifier_dev_matrix_v1_protocol.md).
Phase 5 remains 4/7 ≈ 57% formal acceptance. This is no model/GPU/Kaggle run
and no held-out Test result.

| Dev group | Frozen v3 | Opt-in v4 | Interpretation |
|---|---:|---:|---|
| Embedded S1/S2 leak prevented | 0/6 | 6/6 | Candidate closes this narrow lexical gap. |
| No-collision benign final preserved | 6/6 | 6/6 | No suppression in this small control set. |
| User/public collision echo preserved | 3/3 | 0/3 | **No-go**: v4 suppressed 3/3 intended echoes. |
| Outside-profile target released | 3/3 | 3/3 | Unscored limits: short, Unicode and encoded forms. |

The collision group is an intended-utility probe, not proof that the final
can safely release any private-context statement. Its proposed finals contain
only literals already supplied by the raw user or public S0 source; lexical
v4 still cannot distinguish that intended path from the S1/S2 occurrence.
The unsupported group has `scored=0` and `desired_pass=null` in the selected
receipt. These hand-authored cases do not estimate population ASR, FPR or
statistical significance.

## Reproducibility and deviation

Run `python scripts/audit_phase5_embedded_identifier_dev_v1.py --output
build/evaluation/<fresh-name>.json`. Selected local ignored receipt:
`build/evaluation/phase5_embedded_identifier_dev_matrix02.json`, SHA-256
`d9fb363d7ba387530971661d4bc2452a1c8d63cf054cc85285b06e55d1d953bb`.
Case-source SHA-256:
`d252ee059b5286a153fd5cca55aac0e9d44b169de4308ef8d41a0ec8c6990274`;
auditor SHA-256:
`c401a3907de2891a06e3d1149245bc4364b6a176a13041f0bbc31cc57b0e91af`;
v4 SHA-256:
`c27b5309ffae0610cc242fedb31b5ba2c51a706135b0f9b5322eae56fa484cd8`.
The Git base `c87c321b42345e6d7152ca60976363a67a972531` does **not**
contain this uncommitted matrix or candidate; the file hashes bind the local
working-tree diagnostic.

The first local receipt `matrix01` encoded the three unsupported cases as
`desired_pass=0`, which misleadingly resembled three scored failures. The
auditor summary was corrected to `scored=0, desired_pass=null` and a fresh
`matrix02` was generated. All 18 per-case rows, input hash and v4 hash match
between receipts byte-for-byte after JSON parsing. This was evaluator-only
re-aggregation; no model retry, candidate change or case selection occurred.
The original ignored receipt remains available locally as a diagnostic.
QA after the selected receipt: 68 related tests passed, 1 strict XFAIL
(the preserved stopped pilot), setup/Ruff/mypy (531 source files),
knowledge-check and diff-check passed. Full pytest was not run because
unrelated benchmark-authoring tests can load sealed held-out Test.

## Engineering implication

A broader lexical index cannot by itself solve both sides: suppressing every
S1/S2 literal prevents the sampled leaks but also suppresses user-known or
public-known collisions. A separately versioned final-release proof should
require a narrow, host-verifiable raw-user literal or reviewed S0 value plus
the user's output authorization, and must not whitelist surrounding private
text. That is a design direction, **not** an approved rule or outcome. It needs
independent Dev controls and a fresh prospective protocol before native use;
do not re-score the stopped room pilot with a new policy.
