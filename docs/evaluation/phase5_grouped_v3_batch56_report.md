# Grouped native v3 — shards 5/6 submission

Observed 2026-09-14 20:15 UTC (2026-09-15 Vietnam): both notebooks **RUNNING**,
failureMessage=null. No terminal output audit or semantic result yet.

| Preselected shard | Actual notebook | Version / kernel ID |
|---|---|---|
| 5 QUERYLEAK | [shard-5](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-5) | 1 / 134393202 |
| 6 QUOTED | [shard-6](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-6) | 1 / 134393213 |

Each contains 14 frozen attack/benign × A0–A6 tasks. Source remains
`0d865365b7881144756f804441ca24ed48935f7f`; GitHub main evidence
`80a8bae880c456d63319414ab354c6f865ff3423` was verified remotely before submission.
All 175 source pins, wrapper/metadata pins and exact-package/CPU receipts match.
No new model/prompt/policy/data/dependency changes or semantic retry.

Pre-submit live quota: 25.34 GPU hours. The private
[guard Dataset](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
is ready at **version 1**. Agent model mount
`qwen-lm/qwen2.5/transformers/7b-instruct/1` and bundled guard snapshot remain
unchanged. Both notebooks are private/offline, T4x2, timeout 14,400 seconds, with
the same pinned Docker image. Pulled source hashes and remote metadata match
the frozen packages. Requested aliases `...-s5`/`...-s6` were replaced by the
actual title-derived handles above. GitHub membership does not grant access to
private Kaggle resources; do not make them public for sharing.

## Receipts and continuation

- [Shard 5 submission](../../experiments/manifests/phase5_grouped_v3_s5_submission01.json).
- [Shard 6 submission](../../experiments/manifests/phase5_grouped_v3_s6_submission01.json).
- Access evidence: `results/phase5_grouped_v3_batch56_access01`.
- Original submission logs/receipts: `results/phase5_grouped_v3_batch56_submission01`.
- Remote wrappers/metadata and initial status: `results/phase5_grouped_v3_batch56_monitor01`.
- Prerequisite terminal results: [shards 3/4 report](phase5_grouped_v3_batch34_report.md).

Next action: query these actual handles; do not push again. Once terminal,
verify live current version and source, download every output page to a fresh
batch56 directory, run the existing independent release auditor twice and
generate descriptive JSON/CSV. Preserve semantic errors, check credential
exclusion, guard/tool coverage, startup/generation/task wall timing and lifecycle.
Only then dispatch final preselected shard 7 ROWLIST after live quota/access
checks. Do not grant missing ROWLIST columns from private oracle data.

Audited schedule remains **70/112 (62.5%)**, 50 runtime completed/20 model_error.
The 28 tasks running here do not add to audited coverage. Phase 5 aggregate
gates remain **4/7≈57%**, with quality/lifecycle coverage and freeze outstanding.
No Test/private oracle access or local weight inference in this continuation.
