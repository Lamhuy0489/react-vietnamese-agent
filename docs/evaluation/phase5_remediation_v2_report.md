# Phase 5 — corrective runtime v7 / v2 component QA

Date: 2026-09-13. **CPU repair validation passed; Phase 5 remains unaccepted.**

## Changes and regression evidence

- Clause-bound source/type grants eliminate cross-document and split-incomplete
  authorization. Source namespace is part of the grant, and supplied host grants
  must exactly equal canonical raw-user extraction.
- Final residual screening detects transformed copies even when an authorized
  exact occurrence is also present. No weakening of source trust/sensitivity.
- Table/column pairs prevent analogous A4 cross-table scope expansion. Runtime
  v7 composes scope before Broker at A4–A6, keeps state local, and reports A6
  metadata only for A6.
- Actual read-only smoke DB queries exposed an additional omission: v1 silently
  skipped `SV_SYN_*` student IDs. The bounded v2 index handles these typed/text
  values; unsupported recognized typed fields invalidate coverage.
- Historical v1/v5/v6 code, raw results and receipts were not overwritten.

## Measured CPU checks

| Check | Result |
|---|---|
| Focused regression/runtime/receipt tests | 91 passed, 27.06 s |
| Full development suite | 2,444 passed, 1 skipped, 460.00 s |
| Setup / Ruff / mypy | Pass; mypy covers 314 source files |
| Knowledge structure/links | Pass; current summaries separately reviewed |
| Focused runtime records | 69 runs: 28 v5 comparison + 41 v7 |
| Unaffected exact Replay comparisons | 28 pairs: 7 levels × 4 terminal paths |
| v7 Broker calls in focused artifacts | 41 |
| v7 metadata/guard-closed aggregate checks | 0 mismatches |
| Source/raw receipt re-audit | 436 source + 573 raw hashes, all match |
| Tracked data before/after | 169 file hashes unchanged |

The one skip is `test_worker_progress_v1.py:143`, native tqdm unavailable. This
run does not claim that skipped native behavior was revalidated. Timing above
is QA elapsed time, not LLM/GPU throughput. All runtime backends here are Replay
or synthetic guard; there are no new model, Kaggle, benchmark Dev or Test runs.

## Identity and historical deviation

[New receipt](../../experiments/manifests/phase5_remediation_v2_cpu01.json)
SHA-256: `a027c9f69c682d35b157e108e08a0dfa2ad1ec4d8a7245bac8e01028ba6b2332`.
Raw logs, JUnit and runtime artifacts: `results/phase5_remediation_v2_cpu01/`.
This is explicitly **working-tree CPU QA**, anchored to parent `09c4a51` and
exact file hashes; it is not mislabeled as a clean-source release. The receipt
was independently re-audited after completion with zero mismatches.

`phase5_final_entitlements_v1_validation01.json` fails its actual `pytest.log`
hash (expected `b999c7cf…`, actual `c5e01aea…`); the full values are retained in
the new receipt's historical audit. Both old files remain unchanged. A valid
new repair run does not retroactively validate that old receipt. Runtime v6 and
scope v1 raw/source hashes still match, but byte integrity is not behavioral QA.

## Still required for Phase 5

Production ModelPair/runtime integration and GPU lifecycle, production guard
quality/grouped Dev differential experiments, broader semantic scope/origin
coverage, and formal freeze. The bounded grammar is deliberately conservative;
these tests do not establish general Vietnamese intent parsing or ASR/utility.
The next implementation boundary is documented in
[ModelPair handoff](../../knowledge/phase5_modelpair_runtime_next.md).
