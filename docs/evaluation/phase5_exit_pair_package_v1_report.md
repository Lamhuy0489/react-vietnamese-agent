# ExitPair exact package v1 — 2026-09-20

Development package passed both offline isolated mount rehearsals. This is
packaging evidence, not native GPU execution or Phase 5 acceptance.

- [Contract](../architecture/phase5_exit_pair_package_v1_contract.md).
- [Development receipt](../../experiments/manifests/phase5_exit_pair_package_dev01.json).
- Builder `scripts/prepare_phase5_exit_pair_package_v1.py`.
- Launcher `notebooks/kaggle/exit_pair_probe_kernel_v1.py`.
- Native CLI/auditor and release authenticator are versioned separately; frozen
  constrained worker, model policy and previous experiment identities unchanged.

Package contains 176 worker files and 182 source pins. Each layout validates
eight tools, 21 public clean Dummy tasks, completed immutable resume and
missing-only resume. Each also runs ten fresh ExitPair task controls and retains
six copied terminal checkpoints: valid and deliberate backend failures remain
separate. No real model loads, local GPU, Test or private oracle access.
74 new package/release-boundary tests passed; native GPU behavior is mocked in
those unit tests, not claimed as measured. Cross-host audit binds recorded
interpreter identity. Development launcher rejects native execution.

Read-only remote admission at `results/phase5_exit_kaggle_preflight02` confirmed
owner huylmhuhu, 30.00h available GPU quota, private guard15 Dataset ready/v1.
The sandbox DNS failure in preparation01 remains recorded; it did not submit a
job. Existing constrained notebook remains COMPLETE and must not be resubmitted.
Requested new notebook: `huylmhuhu/react-vn-exit-milestones-v1`; no actual version
is claimed until a successful push and source/metadata verification.

Final [QA](../../experiments/manifests/phase5_exit_pair_package_qa01.json) passed:
763 focused unit/regression tests (46.69s), 180 integration tests (165.33s),
setup, Ruff, mypy467, knowledge links and diff checks. The full repository suite
was not run: sealed Test-authoring fixtures remain excluded. All prior frozen
172/142/86/175 source pins and CPU milestone/pair QA source pins still match.

Next: one required source-freeze commit/push, committed release
rehearsal and read-only package authentication, then one private/offline bounded
T4 submission. No per-status commit, no automatic retry of semantic failures.
