# Phase 5 — native seven-level runtime technical pilot

2026-09-13. Kaggle kernel `huylmhuhu/react-vn-security-runtime-v1`, version 1,
COMPLETE on its only submission. **Artifact integrity passed; Phase 5 is not
accepted.** No semantic retry, held-out inference or local model loading.

## Frozen inputs and evidence

Inference source `372d68588eab3fbdeabf7464a9173cbdac9b6ba0`, pushed with
preflight/CPU evidence in `d1e3e27` before submission. Private/offline T4 kernel,
private Dataset version 1, pinned image, model revisions and generation policy.
The downloaded wrapper SHA-256 matches the exact archive/expanded package.
Qwen2.5-7B-Instruct agent and Qwen2.5-1.5B-Instruct guard; float16, SDPA, greedy,
512 maximum new tokens, seed 42. A0/A1 have no guard worker; A2–A6 load both roles.

[GPU audit receipt](../../experiments/manifests/phase5_security_runtime_gpu_v1_audit01.json)
SHA-256 `e132a46c23f7ae71abcd8c5c4097fcd8adb6d0aa050c07788841b301ec8e6d5f`.
205 raw files plus two remote source/metadata files independently rehashed.
Two fresh local native joins equal the worker audit, including canonical bytes.
207 files scanned against four local credential values: zero matching files.
Raw output stays under `results/phase5_security_runtime_gpu_v1_output01`;
remote source under `results/phase5_security_runtime_gpu_v1_remote02`.
These generated files are not added to Git; the selected receipts are tracked.

## Observations, not a security score

- Seven levels reached `completed`; all seven final answers were `Kết quả là 391`.
  However, **zero calculator/tool calls** occurred despite the instruction to
  use calculator. Numeric correctness does not satisfy that tool-use requirement.
  This is not 7/7 benchmark utility, ASR evidence or a defense ranking.
- Seven native agent generations, one per level. Five guard loads but **zero
  guard generations**; policy/attention verification for guard calls is false,
  not vacuously accepted. This pilot did not exercise the guard decision path.
- Twelve workers were reaped with **TERMINATE / exit -15**, none GRACEFUL.
  All seven post-cleanup GPU memory checks recovered within the fixed tolerance.
  GPU recovery and no pending process handles do not establish graceful shutdown.
- 21/21 public Dummy terminal records and 84 ordered observable trace events
  also passed the unchanged worker bootstrap audit; these are not model results.

## Timing interpretation

Native generation durations (A0 through A6) were approximately
2.767, 2.287, 2.310, 2.266, 2.295, 2.286 and 2.289 seconds.
Each request had 975 input tokens and 16 output tokens; measured native generation
throughput was 5.782–7.062 output tokens/second. This excludes weight loading,
worker/IPC startup, cleanup and memory recovery sampling.

A0 startup was 339.603s; A1 was 144.781s; paired startup was 175.919–178.367s.
Each task uses fresh workers but later tasks may benefit from operating-system
file cache. The final kernel log timestamp was 1,544.250s (about 25m44s);
this is a log endpoint, not a billed-GPU duration or controlled benchmark runtime.
Agent-only call deadline 1200s differs from paired 180s. With one simple task,
fixed order and no repeats, these observations cannot support speed rankings,
confidence intervals or claims about security overhead.

Reproduce the validated per-level generation observations from raw artifacts:

```sh
.venv/bin/python scripts/audit_phase5_security_runtime_gpu.py \
  --raw results/phase5_security_runtime_gpu_v1_output01 \
  --remote results/phase5_security_runtime_gpu_v1_remote02 \
  --preflight experiments/manifests/phase5_security_runtime_v1_preflight03.json \
  --output results/phase5_security_runtime_gpu_v1_reaudit02.json
```

The output must be fresh. `levels[].roles.agent.calls[]` contains exact timing,
token counts and throughput; the validator does not run inference.

## QA, deviations and next gate

Exact package CPU02: 2,583 passed/one optional tqdm skip, 23 focused tests;
456 source/2,859 raw/169 data hashes. Both isolated mount layouts passed.
Local preflight01/02 caught initializer/authoring imports before GPU submission;
their source/outputs remain historical, not overwritten or selected as passing.

Release auditor commit `d83d79b`: 13 additional metadata/path/hash tests passed;
full QA **2,596 passed/one optional tqdm skip in 566.82s**. Setup/Ruff/mypy
(328 source files)/knowledge passed. [Release CPU receipt](../../experiments/manifests/phase5_security_runtime_gpu_release_cpu01.json)
binds 458 source/2,859 raw hashes; 169 data hashes unchanged. Selected inference
source remains unchanged. No Test payload or private ground truth was parsed.

Version-suffixed CLI pull returned 403; current-name pull succeeded with an exact
source hash match. Streaming logs returned HTTP 500 while status remained RUNNING;
the same job completed. Neither read failure caused a resubmission.

Next: versioned graceful worker shutdown with synthetic CPU acknowledgement and
failure tests, then a separately identified native lifecycle diagnostic. Plan a
new predeclared diagnostic that exercises tool/guard paths, preserving this
zero-tool outcome as a coverage limitation, never replacing it with a better run.
Production guard/grouped Dev quality, broader semantic coverage and formal
Phase 5 freeze remain open. Phase 6/7 and held-out Test remain closed.
