# Grouped native v3: submission and release audit

2026-09-14. The worker remains frozen at `0d86536`; GitHub source and preflight
evidence were pushed through `93dc9a2` before submission. The additional release
auditor below is local, read-only, and does not change model/runtime/Dev selection.

## Actual run

[Notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-0),
version 1, kernel ID 134340826; requested alias ended in `-s0`, but Kaggle chose
`-shard-0` from the title. One shard, 14 matched Dev/A0–A6 keys, timeout 14,400s,
private/offline T4x2. [Submission receipt](../../experiments/manifests/phase5_grouped_v3_s0_submission01.json).
Unversioned source pull matches the frozen submitted wrapper SHA-256, and its
private/offline/image/model/Dataset metadata matches. A version-qualified pull
returned 403. Installed CLI status/log methods parse but do not forward the
version argument: do not claim they authenticate a historical session version.

At the latest 14:59:33 UTC check Kaggle reported RUNNING, `failureMessage=null`;
output listing was empty and log length zero. This does not establish completed
task count, whether the worker has started inference, or a failure cause. Do not
retry/overwrite this run or submit the other seven shards while this gate is open.
Raw observations: `results/phase5_grouped_v3_s0_monitor01`, `monitor02`, `monitor03`
(the latter two use the same full prefix `phase5_grouped_v3_s0_`).

## Local terminal auditor

`scripts/audit_phase5_grouped_gpu_v3.py` authenticates the downloaded code without
executing it, compares the submission/preflight pins and local frozen source,
checks the exact bootstrap including model snapshot/wheels, rebuilds the public
Dev identity, and runs the native checkpoint/metrics/policy/lifecycle join twice.
It requires 14 complete checkpoints, canonical agreement with the worker audit,
and an exact immutable output inventory. Semantic model failures remain in the
denominator. Partial/ERROR runs are retained for diagnosis, not declared accepted.

32 focused tests passed during implementation: 25 new release-boundary tests and
seven existing native per-task join tests. Synthetic boundary fixtures are not
model evidence; package identity and model-native metrics have separate checks.
Source `05da583`; [frozen focused QA receipt](../../experiments/manifests/phase5_grouped_release_auditor_v3_cpu01.json)
SHA-256 `7c4ccd8cc5a04dfb27fc7626225c420f342a205123edaa6cf0133d4d041156a2`.
Setup, Ruff, mypy393 and knowledge checks passed, source/raw/data hashes re-audited.
Full worker QA remains the earlier 3,113 pass/one skip
receipt, not a claim that the new local auditor has been included in that run.

Once terminal, download all output to a fresh directory, preserve its status/log,
re-pull source, and run the auditor with the frozen preflight and submission
receipts. It never repairs raw output or runs inference. Independently scan
downloaded artifacts for credential values before selecting release evidence.
If accepted, summarize task status, Pre/Post/Final structured-output failures,
startup/generation/end-to-end seconds, worker retirement and VRAM recovery.
ASR/FPR/utility and Phase 5 freeze remain separate gates; aggregate stays 4/7.
