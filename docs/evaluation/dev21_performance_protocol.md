# Dev21 performance protocol v1 — 2026-09-06

Owner authorized Gemma 4 and a larger Qwen, with latency and efficiency reporting.
These conditions supersede the unexecuted Gemma 2 pilot. No model outputs from
the new conditions were observed before this protocol was written.

## Conditions

- Gemma 4 E4B IT: `google/gemma-4/transformers/gemma-4-e4b-it/1`.
- Qwen2.5 7B Instruct: `qwen-lm/qwen2.5/transformers/7b-instruct/1`.
- Meta Llama 3.2 3B IT remains pending account access, not a completed comparison.
- Historical Qwen2.5 3B is a reference only; it lacks the new instrumentation
  and pinned software environment and cannot establish a controlled speed gain.

Same 21 clean_v1.1 Dev IDs, order, environment, fault plans, A0, max 8 steps,
2 schema retries per step, max 512 generated tokens per call, batch 1, seed 42,
greedy decoding, thinking disabled. These controlled settings are not a claim
of each manufacturer's recommended or best achievable settings. No Test model
access, prompt tuning or final-model selection is part of this pilot.

Float16 unquantized, SDPA, two NVIDIA T4 GPUs, balanced automatic model placement
with 13 GiB per device, CPU/disk offload forbidden. Record actual device map,
parameter count, GPU memory size, CUDA/PyTorch and tokenizer versions. Total
parameter counts differ; E4B has approximately 8B parameters including embeddings.
Gemma 4 uses its native system-role template; Gemma 2's adapter is not applied.

Transformers 5.5.0, tokenizers 0.22.2, huggingface-hub 1.7.2, accelerate 1.10.1,
regex 2025.11.3, safetensors 0.6.2 and hf-xet 1.4.2 are installed from hashed
offline wheels. Keep the Kaggle image's PyTorch/CUDA and record their versions.
CPU loader preflight uses actual mounted tokenizers/configs and two randomly
initialized tiny models; it does not generate on any benchmark task.

## Measurements

- Separate model load and one fixed 16-token synthetic warm-up from task timing.
- Every generation synchronizes CUDA before/after, records monotonic elapsed
  generation and whole-call time, exact input/output token counts and per-GPU
  peak allocated/reserved bytes. Output count includes generated special tokens.
- End-to-end task time uses run_start/run_end trace timestamps and includes
  tool execution, format retries and observable logging. Report mean, sample
  standard deviation, median and linear-interpolated p95 across all 21 tasks.
- Throughput = total generated tokens / summed synchronized generate seconds;
  this includes prefill, not decode-only TPS. Tokenizers differ; report token
  counts and avoid interpreting TPS as equal useful work across models.
- Report all-task and successful-task latency separately so early failures
  are not mistaken for useful speed. No TTFT or energy metric is claimed.
- Single invocation per model/task after warm-up. Latency spread describes
  task variation, not repeated-run hardware variance. No cherry-picked retries.

## Quality and uncertainty

Use frozen `clean_v1_1_typed_v1` evaluator on local private Dev GT. Report strict
task success, per-category success (3 examples each), output schema validity,
terminal parse failures/max-steps/model errors, wrong tool/argument indicators,
and overlapping failure reasons. Strict success includes annotated tool paths;
correct final facts alone can still fail this rubric.

95% percentile bootstrap intervals use 5,000 resamples, seed 2026, sampling
semantic `instance_group_id` clusters with replacement and keeping their tasks
together. Paired success/latency differences use aligned IDs and the same groups.
Intervals describe this small selected Dev set; they do not estimate final
held-out performance. No significance claims or model ranking based solely on
this pilot. Export JSON, CSV and a source-linked Markdown report from audited
raw outputs with exact hashes; never manually replace measured values.

## Sources and constraints

- Google DeepMind, *Gemma 4 E4B model card*, accessed 2026-09-06:
  https://huggingface.co/google/gemma-4-E4B-it — native system messages,
  parameter interpretation and thinking control. Kaggle version is independently
  pinned; later Hugging Face template edits are not substituted into it.
- Hugging Face, *Gemma4 documentation*, accessed 2026-09-06:
  https://huggingface.co/docs/transformers/model_doc/gemma4 — model class support.
- Official Kaggle file listings (2026-09-06) confirm access to both pinned models.
  Gemma E4B weights are about 16.0 GB, motivating the two-GPU memory preflight.
