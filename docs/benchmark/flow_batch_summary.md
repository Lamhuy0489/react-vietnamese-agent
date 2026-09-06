# Authorization-flow batch and 48-candidate pool

2026-09-06. Phase 3 unsplit authoring, not final family acceptance.

Eight new paired workflows compose the existing source builders, runtime and
private scorers without changing them. They cover separate channel grants,
explicitly allowed private final output, crossed two-artifact grants, aggregate
versus record-level disclosure, commit-before-notify, conjunctive prerequisites,
current-source binding and permitted suffix versus full-token disclosure.

The batch README records assistant pair self-review. Existing group edges are
retained: five artifact-scope cases join authorized-sink-scope expansion, two
ordering cases join premature-commit, one joins business payload substitution.
The combined **48 working candidates remain in 15 conservative review units**;
1,128 pair comparisons are not a certificate of independent final families.

## Verification evidence

- Unified pool: **192 fresh Replay paths**, 96 safe/96 negative; new batch
  contributes 32 paths. All required sources are actually observed, all
  reference calls succeed, and no reference action is unassessed.
- Full suite: **341 tests**, including 20 new parametrized cases. Setup, Ruff,
  mypy (123 source files), knowledge checks and clean v1.1 seal validation pass.
- Nine historical receipts checked: **566 hash entries match**, including the
  twelve measured model-release artifacts. No old data/scorer/model score changed.
- Tests cover directional and final grants, evidence for a privately permitted
  final fact, two artifacts in one call versus two calls, failed/late prerequisite,
  current final answer plus wrong submission, wrong suffix, broken sidecars,
  no network, fresh inputs and normalized trace reproducibility.
- Selected receipt: `experiments/manifests/phase3_pool_v3_validation01.json`.
  Source/input/trace hashes are recorded; preflight and selected runs are separate
  and raw outputs remain ignored. No overwrite or semantic model retry occurred.

The final-grant case intentionally allows an S2 value in the final response
because the synthetic user explicitly authorized that sink. It still forbids
the same value in email. Sensitivity alone does not decide authorization.
Summary and suffix cases are bounded known-value examples, not general privacy,
de-identification, semantic lineage or arbitrary business approval claims.

## Remaining work

48/70 ≈ 69% of the candidate-count target, not accepted-family or whole-phase
completion. Keep the rough Phase 3 effort estimate at **45–50%**, explicitly
unweighted and not a research metric. Twenty-two candidates are still missing
before final family admission/merge decisions; some near-template candidates
may need replacement rather than automatic admission. Then grouped 40/30 split,
350 attack + 350 matched benign variants, equivalence QA and sealed release.
`qa_valid=true` remains distinct from `phase3_accepted=false`.
