# Phase 2 Acceptance Report

Status: **acceptance withdrawn on 2026-09-05; clean_v1.0 quarantined**.

The static audit found 30 fact/evidence-equivalent pairs with different group
IDs, 12 crossing Dev/Test. The old signature included task-local fact labels.
Frozen inputs are preserved; no Test inference or in-place repair occurred.
See `../knowledge/integrity_audit_20260905.md` for current evidence and next work.

## Dataset gates

- Pool: 250 tasks with exact `40/40/50/40/25/30/25` category quotas.
- Split: 150 Dev and 100 Test using stratified group assignment, seed 2026.
- Public/private join: 250/250.
- Schema validity: 250/250.
- Deterministic oracle validity: 250/250 through Tool Broker.
- QA records: 250/250 exist, but generator-assigned flags do not prove QA ran.
- Exact and accent-insensitive duplicates: zero.
- Fuzzy queue: 24 lexical pairs; differing signatures do not prove independence.
- Dev/Test overlap: zero task IDs and declared groups, but 12 semantic instances.
- Environment: 50 documents, 25 cached pages, eight SQLite tables, offline.

Independent review was explicitly waived because Huy and Minh share one
machine. Records use `automated_checks_owner_waiver` and `automated_gate`; they
do not claim a human inspected each task. This is disclosed as a limitation.

## Frozen identity

- Benchmark: `clean_v1.0`
- Dataset hash: `2a98633481ac82ae77dbbbe96877d67a3353894ce869e54947e0cf5335371c62`
- Public Test SHA-256: `a17cc65bdb54b0d6c0a2c55dddeea0e34e2e3763136e2104ffe5fdda316a3ae9`
- Private Test GT SHA-256: `5736c589c5444eaff3d4e1f0427eaa01da12c8cdb71a1465c69bf01c909cebd0`
- Environment manifest SHA-256: `4241e73fa3ada87dd9d595d5db0a249966a5cead7da04a37cba7cac020b787e9`
- Frozen component source: `5354c0e00faf7ea77ab7063b4c583e9783c0a1ec`

## Dev-only Kaggle pilot

The historical run is Kaggle Dataset v2 and kernel v2, Qwen2.5-3B-Instruct v1,
NVIDIA T4, internet disabled. The allowlisted worker bundle contained public
Dev and environment only—no Test, pool, reviews, or private ground truth.

- 21/21 terminal runs; zero model crashes.
- 17 completed, one parse failure, three max-step exits.
- Schema-valid output rate: 87.36%.
- 334/334 trace events schema-valid with correct Tool Broker ordering.
- Provisional diagnostic success: 7/21; not a validated strict TSR.
- Argument presence is not argument correctness; substring matching is not
  the typed fact comparator contract. These remain acceptance work.
- Exact scan of four credential secret values across artifacts: zero matches.

Kernel v1 failed when the fault wrapper did not delegate parser argument
validation. Commit `aa333024c74f08213255d7b580cbfbb521426ed5` fixed the adapter;
local regression tests and kernel v2 then passed. No Test observation informed
the fix.

Raw artifacts remain ignored at `results/phase2/kaggle_v2`. Their hashes and
the complete audit record are frozen in
`experiments/manifests/phase2_kaggle_v2.json`.

## clean_v1.1 replacement acceptance (2026-09-06)

The quarantined v1.0 was not repaired in place. The replacement `clean_v1.1`
is independently generated and sealed with 250 tasks (150 Dev/100 Test), exact
category quotas, executable oracle QA 250/250, and group-disjoint split hashes.
Its dataset hash is recorded in `experiments/manifests/phase2_clean_v11_kaggle_v1.json`.

The same-machine owner waiver replaces human peer review with deterministic
automated checks; this does not claim independent language-quality review.
The Dev-only Kaggle pilot completed and was audited (21 terminal tasks, 0 model
errors, 318 valid trace events, 5/21 diagnostic success). No Test inference or
Test-driven tuning occurred. Phase 2 is accepted for the frozen benchmark;
the pilot score remains diagnostic and is not a final Test result.
