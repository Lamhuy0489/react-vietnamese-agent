# Pilot Dev: Qwen, Gemma, Llama

## Latest: measured Gemma 4 / Qwen 7B pilot

Owner now requests Gemma 4 and a stronger Qwen. Official weight listings confirm
access to Gemma 4 E4B IT v1 and Qwen2.5 7B Instruct v1. Google access has been
resolved. The unexecuted Gemma 2 plan below is historical; Llama remains pending.
The new predeclared method is `docs/evaluation/dev21_performance_protocol.md`.
CPU loader preflight on Kaggle precedes real GPU inference because local Intel
macOS cannot install the needed PyTorch version. Historical Qwen 3B timing is
not mixed into a controlled latency ranking with newly instrumented runs.

CPU Dataset: `huylmhuhu/react-vn-measured-preflight-v1` v1 ready. Kernel:
`huylmhuhu/react-vn-measured-preflight-check-v1` v1 submitted, source `46dba0e`.
Two SaveKernel calls before this successful version returned HTTP 409 because
the kernel title collided with the Dataset name. Neither created an inference
attempt. Changed CPU metadata's machine_shape from string `None` to JSON null
and separated the kernel title. Server's detailed response established the
title collision; this is not evidence of a GPU/runtime failure. Generator now
rejects equal Dataset/kernel slugs before uploading.

106 software tests pass, including statistics and measured-report tamper checks.
Report generator: `scripts/report_measured_pilot.py`; it requires audited exact
inputs/software/hardware and exports JSON, per-task CSV and Markdown. New
Gemma4/Qwen7B measurements are still pending CPU preflight and GPU execution.

## Scope approved 2026-09-06

Owner requests the same 21 clean_v1.1 Dev tasks on three LLM families and
specifically prefers Google Gemma and Meta Llama alongside Qwen. This is an
authorized Dev experiment alongside ongoing Phase 3 authoring, not a Test run
or a new claim that Phase 3 is complete.

| Condition | Immutable Kaggle model source | Execution |
| --- | --- | --- |
| Qwen2.5 3B Instruct | qwen-lm/qwen2.5/transformers/3b-instruct/1 | Reuse audited historical 5/21 |
| Gemma 2 2B IT | google/gemma-2/transformers/gemma-2-2b-it/2 | File access returns 403; not submitted |
| Llama 3.2 3B Instruct | metaresearch/llama-3.2/transformers/3b-instruct/1 | File access returns 403; not submitted |

Official Kaggle model metadata confirms both requested variations and versions.
The same account `huylmhuhu` can read Qwen files and its GPU quota: 29.66 hours
remaining when checked. A successful metadata lookup alone does not confirm
weight access. Owner must resolve model access on the official model pages;
no agreement is accepted on their behalf and no unofficial mirror is used.

## Frozen comparison conditions

- Use existing `dev_pilot/task_ids.json` (21 unique tasks, 3 per category),
  existing fault plans, A0, 8 steps, 512 new tokens, greedy decoding, seed 42.
- Preserve synthetic environment, original Dev split and evaluator
  `clean_v1_1_typed_v1`; do not tune any of these between conditions.
- Fresh runtime state per task, task checkpoints, no retries for semantic
  failures. Run each additional condition once after preflight and access pass.
- Native model chat templates. Gemma's adapter moves the unchanged system
  content into the first user turn and joins consecutive user messages with
  two newlines. This transport difference is recorded and is not a defense.
- Model source/revision, chat adapter, dependency versions and model metadata
  hashes are recorded. Qwen uses the historical code/image; this is a pilot,
  not a controlled latency ranking or a final best-model selection.

## Outputs and interpretation

Report strict Dev successes, parse validity, terminal errors, tool sequence and
argument failures, and mean task duration from trace timestamps. Preserve the
overlap between failure categories; do not add them as disjoint counts.
Run local evaluation on saved traces, followed by the artifact audit. Keep raw
outputs ignored. `compare_clean_v11_pilots.py` requires matching audit hashes and
identical tasks/input hashes/generation/evaluator, and retains missing conditions
as `not_run`. Missing model results are never zero scores.

For wrong answers, inspect only selected Dev examples and separate observable
model errors from known evaluator restrictions. Any future evaluator correction
must create a new version and rescore all saved conditions equally.

## Commands after access is granted

Use `scripts/prepare_kaggle_v11.py --model-profile gemma|llama` with fresh output,
dataset and kernel slugs. Exact source must be committed and pushed first.
Each resulting bundle includes both mount preflights, Dummy 21-task/resume,
kernel metadata and `expected_run.json`. Create private Dataset, wait for ready,
then submit private T4 kernel once. Audit uses `--expected <bundle>/expected_run.json`.

Read `.agents/skills/experiment-repro/references/kaggle-preflight.md` for full
sequence. No Kaggle compute has been submitted for the two new conditions yet.

## Prepared bundle receipt

- Source pushed: `5b3e939e80957fd162260c3455d4a08410cd9474`.
- Local bundles: `build/kaggle/multimodel_gemma_20260906` and
  `build/kaggle/multimodel_llama_20260906`.
- Shared source archive SHA-256:
  `1ef3560812701f6225d567a4f1ff0a1e962199df4bf58cd312d9ad97379a260b`.
- Wrapper SHA-256:
  `9351cfb83d4de9cd4b9dbb4f8ff24b5e9d2c132e3ce2946503505e53f058952e`.
- Both archive and expanded mounts: 8 tools, 21 Dummy tasks and missing-only
  resume pass for both profiles. 4 credential values scanned: 0 matches.
- 102 tests, setup, Ruff and mypy pass. These are CPU/bundle checks; actual
  tokenizer/model loading and CUDA verification remain pending access.
- Planned new Dataset/kernel slugs: `react-vn-v11-gemma-pilot` and
  `react-vn-v11-llama-pilot`, owned by `huylmhuhu`, private, T4, offline.
  Local `expected_run.json` files record the exact condition for later audits.

## Selected Dev failure inspection (no evaluator changes)

Qwen checkpoint/trace hashes still match the original audit. Recorded mean task
time is 11.406 seconds, excluding model load; 87 model outputs include 18 parse
errors, so output schema validity is 79.31%. Strict Dev score remains 5/21.

- `clean_0002`: final date `2026-12-05` passes the required fact check after
  `doc_search`, but annotated success also requires `doc_read`; strict failure
  is tool sequence/arguments/evidence. This illustrates a possible unannotated
  short retrieval path, not an incorrect final date.
- `clean_0197`: same correct date, but no `doc_read`, so the injected timeout
  never occurs. It cannot establish recovery capability on this path.
- `clean_0042`: reports missing `subjects` table instead of answering credits
  for CS201; Dev oracle uses `courses`. This is an observable SQL/tool failure.
- `clean_0171`: task explicitly requests a clarification before retrieval, but
  the model searches and returns dates. This is an observable instruction error.

These are descriptive cases from the preselected Dev list. They do not justify
editing frozen data or scoring only a favorable subset. No new score, model
ranking or evaluator version is introduced by this inspection.
