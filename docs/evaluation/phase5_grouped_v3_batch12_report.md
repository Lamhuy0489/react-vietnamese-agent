# Grouped native Dev — shards 1 and 2

2026-09-15 (Asia/Ho_Chi_Minh); terminal status read 2026-09-14 18:41 UTC.
Same frozen source `0d865365b7881144756f804441ca24ed48935f7f`, preselected public
Dev pairs, agent/guard pins, runtime v10 and greedy generation as shard 0.
No prompt/policy/data change, semantic retry, Test inference or oracle scoring.

## Audited results

| Measurement | Shard 1 SOURCEBINDING | Shard 2 DATABASE |
|---|---:|---:|
| Terminal checkpoints | 14/14 | 14/14 |
| Runtime completed / model_error | 4 / 10 | 14 / 0 |
| Executed tool calls/results | 16 | 14 |
| Returned guard classifications | 10 | 21 |
| Valid guard responses | 0 | 21 (11 PRE, 10 POST) |
| Invalid guard responses | 10 JSON-syntax errors at PRE | 0 |
| Additional guard failures without returned output | 4 POST BACKEND_FAILURE | 0 |
| Worker shutdowns | 23 GRACEFUL, 1 TERMINATE | 23 GRACEFUL, 1 TERMINATE |
| Reaped workers / stable VRAM recovery | 24/24 workers; 14/14 tasks | 24/24 workers; 14/14 tasks |
| Task wall time sum, including setup/cleanup/recovery | 2,517.02s (41.95min) | 2,536.09s (42.27min) |
| Startup time sum | 2,309.87s | 2,302.93s |
| Agent generation time / output tokens | 72.10s / 630 | 87.49s / 835 |
| Agent aggregate tokens/generation-second | 8.74 | 9.54 |
| Guard generation time / output tokens | 15.12s / 310 | 23.67s / 567 |
| Guard aggregate tokens/generation-second | 20.51 | 23.96 |
| Raw / remote files independently authenticated | 566 / 2 | 678 / 2 |

Native joins, source/bootstrap pins, exact task coverage, repeated audit equality
and worker audit equality all passed. Hashes were independently rechecked and
credential-value scanning found zero matches in 1,248 raw/remote files.
No downloaded code was executed locally, and no local weights were loaded.

## Interpretation and limits

SOURCEBINDING A0/A1 complete (four tasks). All A2–A6 tasks stop with model_error:
each returned PRE guard response fails JSON syntax, not model loading. The
structural diagnostics record 94 characters in each response; they deliberately
retain no raw guard text, so the precise malformed string is unknown. A2/A3
attack/benign traces then contain four POST BACKEND_FAILURE outcomes after pair
retirement. Those are additional failed classifications, not additional returned
guard responses. They must not disappear from the failure denominator.

DATABASE now establishes real tool/guard PRE/POST path execution, unlike shard
0's zero-tool run. However, valid JSON and terminal completed are not semantic
task success, correct risk classification, attack resistance, or benign utility.
These are one-pair descriptive observations, not a controlled backbone ranking,
ASR/FPR estimate or confidence interval. Model native execution success and guard
classification success are separate: the ten invalid SOURCEBINDING responses
still have authenticated generation metrics, not successful classifications.

Across shards 0–2: **42/112 scheduled tasks (37.5%) have native terminal audits**;
32 runtime completed, 10 model_error; 30 executed tool calls; 31 returned guard
responses (21 valid, 10 invalid), plus four no-response backend failures.
All 72 workers reaped (68 graceful, four terminated); all 42 tasks recovered VRAM.
This coverage percentage is **not** Phase 5 acceptance: aggregate gates remain
4/7≈57%, with broader guard quality/lifecycle coverage and freeze outstanding.

## Links and immutable evidence

- Shard 1 [notebook v1](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-1),
  kernel ID 134350547; [submission](../../experiments/manifests/phase5_grouped_v3_s1_submission01.json),
  [audit](../../experiments/manifests/phase5_grouped_v3_s1_audit01.json),
  [summary](../../experiments/manifests/phase5_grouped_v3_s1_summary01.json),
  [terminal scan/hash evidence](../../experiments/manifests/phase5_grouped_v3_s1_terminal01.json).
- Shard 2 [notebook v1](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-2),
  kernel ID 134350561; [submission](../../experiments/manifests/phase5_grouped_v3_s2_submission01.json),
  [audit](../../experiments/manifests/phase5_grouped_v3_s2_audit01.json),
  [summary](../../experiments/manifests/phase5_grouped_v3_s2_summary01.json),
  [terminal scan/hash evidence](../../experiments/manifests/phase5_grouped_v3_s2_terminal01.json).
- Both use the private [guard Dataset v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1),
  Qwen model variation v1, offline T4x2 and 14,400s notebook timeout. Requested
  aliases `...-s1`/`...-s2` were replaced by title-derived actual handles above.
- Download root `results/phase5_grouped_v3_batch12_download01/raw_s1` and `raw_s2`;
  remote/status snapshots in `results/phase5_grouped_v3_batch12_monitor01`.
  Summary CSV/JSON in `results/phase5_grouped_v3_s1_summary01` and `s2_summary01`
  (both use the full `phase5_grouped_v3_` prefix).

No worker source changed. Setup/Ruff/mypy394/knowledge and 35 relevant tests pass;
[previously frozen summary QA](../../experiments/manifests/phase5_grouped_summary_v3_cpu01.json)
rechecked 562 source/raw hashes. Full worker QA remains the existing 3,113 pass/
one optional skip receipt; no redundant full rerun or promotion of focused QA.

## Next step

Retain all three terminal runs. Continue preselected shards 3 ENCODED and 4
LINKPAGE with unchanged packages after a live quota/mount check and GitHub push.
No repeated semantic attempts, threshold/prompt repair, or data change is part of
this expansion. Audit terminal artifacts before dispatching shards 5–7.
