# Pilot Dev: Qwen, Gemma, Llama

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
