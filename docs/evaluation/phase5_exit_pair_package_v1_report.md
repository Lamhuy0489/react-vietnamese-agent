# ExitPair exact package v1 — 2026-09-20

Update2026-09-21: native v1 COMPLETE and independently audited; see
[terminal report](phase5_exit_gpu_v1_report.md). The submission-time RUNNING and
pending-download notes below are historical. No resubmission is needed.

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

Source freeze `6d039e255a0a0a91f6e514cfebe889c4b7ae8aed` was committed and pushed
to GitHub main exactly once. [Committed release rehearsal](../../experiments/manifests/phase5_exit_pair_package01.json)
passed both layouts and the read-only 182-source-pin package authenticator.

## Native submission

At 2026-09-20 16:57:50 UTC, actual
[huylmhuhu/react-vn-exit-milestones-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-exit-milestones-v1)
version 1 / ID135130970 was **RUNNING**, private/offline/T4, timeout3600s.
[Submission receipt](../../experiments/manifests/phase5_exit_gpu_submission01.json)
binds code hash, version, Dataset v1, source commit and QA. Remote source and
settings match the release package; latest-session status is a dated observation,
not proof of completion. Output has not yet been downloaded/audited.

The push API returned `/code/owner/slug` for its ref. A strict host-side equality
check stopped after the successful push. Retained `intent.json` and
`push_response.json` prove one accepted submission. A separate read-only check
normalized that prefix and authenticated the remote code/metadata/version;
**no second push or GPU retry**. Raw records: `results/phase5_exit_gpu_submission01`.

Next: observe this version, retain terminal outputs in a fresh directory and run
two independent `audit_phase5_exit_gpu_v1.py` audits. Do not resubmit either old
or new notebook while this job is pending. Compare role-bound target/finalizer/
thread-shutdown milestones before proposing a lifecycle fix. No native root-cause,
guard quality or Phase 5 acceptance claim yet. Post-freeze receipts/memory remain
local pending the next meaningful closeout; no status-only commit.
