# Grouped native v3 — shards 3/4 submission

Observed 2026-09-14 19:03 UTC (2026-09-15 in Vietnam). Both notebooks are
**RUNNING**, failureMessage=null. This is submission/source evidence, not terminal
acceptance or a quality result. No output has been downloaded or scored yet.

| Frozen Dev shard | Actual notebook | Version / kernel ID |
|---|---|---|
| 3 ENCODED | [shard-3](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-3) | 1 / 134383821 |
| 4 LINKPAGE | [shard-4](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-4) | 1 / 134383829 |

## Identity and checks

- Worker source `0d865365b7881144756f804441ca24ed48935f7f`; source/evidence on
  GitHub main `707859311be626ea03dc60ab9712fd40370f4533` verified before push.
- Existing [exact-package preflight](../../experiments/manifests/phase5_grouped_package_v3_preflight01.json)
  and [full CPU QA](../../experiments/manifests/phase5_grouped_package_v3_cpu01.json)
  retained. All 175 source pins and both notebooks' wrapper/metadata pins
  rechecked before dispatch. No worker, prompt, policy, data, or dependency edits.
- Pre-submit quota 26.79 GPU hours; private
  [Dataset guard15 v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
  live ready/version 1. This quota snapshot is not a reservation.
- Qwen2.5-7B model variation `qwen-lm/qwen2.5/transformers/7b-instruct/1`, bundled
  guard snapshot and offline wheels unchanged. Each notebook private/offline,
  T4x2, timeout 14,400 seconds; pinned Docker image unchanged.
- Both pulled remote wrappers match the frozen local bytes; remote metadata
  confirms private/offline, Dataset/model sources, machine shape and Docker pins.
- Requested aliases `...-s3`/`...-s4` were replaced by title-derived actual
  handles above. No second push; neither shard is a semantic retry.

## Evidence and next action

[Shard 3 submission](../../experiments/manifests/phase5_grouped_v3_s3_submission01.json)
and [shard 4 submission](../../experiments/manifests/phase5_grouped_v3_s4_submission01.json)
record original submission hashes, observed status/time, remote metadata/source
hashes, prior shard audits and access evidence hashes.

Local immutable observations:

- `results/phase5_grouped_v3_batch34_access01`: quota/Dataset snapshot.
- `results/phase5_grouped_v3_batch34_submission01`: original push logs/receipts.
- `results/phase5_grouped_v3_batch34_monitor01`: pulled remote source/metadata and
  RUNNING status snapshots. Use a fresh monitor directory for later observations.

Next: query the actual handles without resubmitting. After terminal, download
all outputs into a fresh batch34 directory; preserve failures, verify version
identity and run `scripts/audit_phase5_grouped_gpu_v3.py`, then the read-only
`scripts/report_phase5_grouped_gpu_v3.py`. Record credential scan, hashes, native
guard/tool coverage and timing before dispatching shards 5–7.

Already audited coverage remains **42/112 (37.5%)**, with 32 completed and 10
model_error. These 28 newly submitted tasks do not count as audited results.
Phase 5 aggregate gates remain **4/7≈57%**; no quality/freeze gate is promoted.
Private resources require Kaggle access independently of GitHub membership.
