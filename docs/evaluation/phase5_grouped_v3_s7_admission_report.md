# Grouped v3 shard7 ROWLIST — admission recovery

**Terminal update2026-09-15:** ROWLIST R3 v1 COMPLETE05:53:41UTC/audit đạt,
không còn pending. Xem [full schedule report](phase5_grouped_v3_complete_report.md)
và [terminal receipt](../../experiments/manifests/phase5_grouped_v3_s7_terminal01.json).
Các đoạnRUNNINGbên dưới giữ lịch sử admission, không phải chỉ dẫn chạy lại.

2026-09-15. Source `0d865365b7881144756f804441ca24ed48935f7f`; 14 preselected
Dev tasks, all A0–A6 attack/benign branches. **Attempt03 admitted v1, RUNNING**
at2026-09-15 05:06:57UTC; no terminal output audit or task results yet.

## Preserved attempts

1. `results/phase5_grouped_v3_s7_submission01/push_s7.log`: Kaggle reported
   `Maximum batch GPU session count of 2 reached` while shards5/6 were running.
   CLI exit0 did not mean successful submission; no version/URL success line.
2. `results/phase5_grouped_v3_s7_submission02/push_s7.log`: after shards5/6
   COMPLETE, SaveKernel returned HTTP409 Conflict. No version/session confirmed.
3. New matching title/slug admitted **version1**, kernel ID134443063:
   [react-vn-grouped-dev-v3-rowlist-r3](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-rowlist-r3).
   R3 labels admission attempt3, not the A3 defense condition. GitHub evidence
   `875399dfeeb0a5feb99c674a479c90ab72ceef94` verified before submission.
   [Submission/status/source receipt](../../experiments/manifests/phase5_grouped_v3_s7_submission03.json).

Owner first allowed concurrency, then requested waiting after Kaggle rejected
the third simultaneous GPU batch. This account's observed cap was two; quota
hours and concurrent-session limits are different controls. Do not generalize
this observation to every account or cycle credentials to avoid it.

Read-only observations in `results/phase5_grouped_v3_s7_admission01` and
`results/phase5_grouped_v3_s7_conflict01`: requested alias GetKernel403, historical
title-derived GetKernel500 and status404, no shard7 among147 returned list entries.
These do not prove absence; a reserved/incomplete name is only a hypothesis.
List response fields id/version/private default to0/0/false even for known
private audited notebooks; never use those defaults to infer privacy/version.

Fresh access snapshot `results/phase5_grouped_v3_s7_access02`: Dataset
[guard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
ready/v1, quota23.83h; shards5/6 COMPLETE at04:51UTC. All five successful prior
source identities remain untouched. No private resources were made public.

## Bounded replacement

[Launcher delta / failure hashes](../../experiments/manifests/phase5_grouped_v3_s7_launcher03.json)
binds the original preflight, unchanged wrapper and metadata id/title-only
replacement under `build/kaggle/phase5_grouped_v3_s7_launcher03`.
No model, data, source, decoding, tool, environment or topology changes. Existing
archive/expanded fresh-venv and full-QA evidence applies to identical executable
bytes; do not claim a new full rehearsal was run for changing a remote address.
Private/offline T4x2, model v1, pinned image and14,400s timeout retained.

Pulled wrapper hash matches the original frozen shard7 executable; remote
metadata confirms private/offline, T4, image and Dataset/model pins. Initial
status is RUNNING/failureMessage=null. Raw push/receipt in
`results/phase5_grouped_v3_s7_submission03`; remote/status in
`results/phase5_grouped_v3_s7_monitor01`. Both earlier failed identities remain
unchanged. Successful new-address submission does not prove why the old409 arose.

Next: monitor **actual ROWLIST R3 handle**, not the rejected `...-shard-7` alias.
Do not push again. At terminal, verify live version, download every output page
into a fresh directory, run existing release auditor twice using submission03,
then descriptive summary/scan. Audit log filename follows actual rowlist-r3
handle; semantic shard index stays7. Only after audit count the final14 tasks.
All112 tasks have now been submitted in eight admitted notebooks;98/112(87.5%)
are audited,14 still pending. Phase5 stays4/7≈57%, not accepted. No Test/private
oracle access, new model conditions or ROWLIST grant changes.
