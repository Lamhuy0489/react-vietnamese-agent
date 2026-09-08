# Phase 5: offline guard adapter v1

Status: technical adapter, not a selected production guard or Phase 5 acceptance.
Prior source, prompts, policies, runtime v5 and measured pilot remain unchanged.
Only synthetic CPU tests are in this milestone; no benchmark payload is loaded.

## Interfaces and boundaries

- `GuardSnapshot`: explicit HF commit plus sorted per-file SHA-256/size inventory.
  `describe_snapshot` describes a **trusted acquisition**, not publisher authentication.
  A future acquisition receipt must independently bind files to the official revision.
- Only a flat, materialized Qwen2.5-1.5B-Instruct snapshot is supported. All seven
  runtime files are required; LICENSE/README/.gitattributes are optional but hashed
  when present. Extra files, symlinks, shards, remote code and quantized configs
  are rejected. Materialize HF cache links before validation; do not relax checks.
- `GuardHFFactory(model_path, snapshot, config, metrics_path)` is picklable and
  implements the existing `Callable[[], LLMBackend]` interface. Pass it to a
  **task-local WarmGuardBackend**, with `snapshot.model_revision` as the worker
  revision. No changes to runtime v5 or guard prompt/cache/decision semantics.
- `GuardHFConfig` binds device, allocator ceiling, free headroom and context cap.
  Default candidate: logical CUDA device 1, 5 GiB allocator ceiling, 1 GiB extra
  free headroom, 4,096 input tokens. These are declared engineering budgets,
  **not measured fit or an agent/guard combined allocation plan**.

## Loading and generation

Hash verification occurs before importing/loading optional HF dependencies and
again after loading. The snapshot mount must remain immutable throughout the
task. This is not protection against a hostile filesystem changing files between
verification and use. Read-only Kaggle inputs are the intended mount contract.

Native `Qwen2ForCausalLM`, local-only tokenizer, safetensors, FP16, SDPA, explicit
single-GPU placement, eval mode. Reject parameters/buffers on another device.
No CPU/disk offload, quantization, download, automatic retry or alternate model.

The CUDA allocator ceiling is **process-wide**: instantiate only in the guard
subprocess, never in the agent process. It does not cap CUDA context overhead or
another process, reserve memory for the agent, or guarantee no OOM. Check global
free memory after CUDA initialization and before load. The previous two-T4
`MeasuredHFBackend` with 13 GiB/device is not a coexistence adapter.

Every generation receives copied complete messages, a newly constructed HF
generation config and a new dynamic cache. There is no stored conversation,
input tensor, returned KV state or generation config reused across calls. Greedy
128-token generation, seed 42, one beam; no sampling or silently inherited
penalties. Tokenizer truncation is explicitly off; reject configured/model
context overflow before GPU generation. No hidden-state/attention output.
Unexpected reasoning markers reject output without saving that content.

Only one generation at a time. Any generation exception retires the backend;
the warm wrapper owns cancellation/timeout/cleanup and invalid-JSON retirement.
No decoder rewrite/JSON repair; the existing strict guard parser is authoritative.

## Measurement and acceptance

Fresh per-task JSONL metrics outside model input; flush/fsync each record. Load
includes both snapshot hash scans. Generation records input/output tokens,
generation/call time, process allocation/reservation peaks and global free-memory
samples. No prompts, generated text, exception text or development memory enter
metrics. Missing success metrics fail closed. Worker attempts provide inclusive
request time, including process startup/load and termination on failure.

Process allocator peaks exclude other processes. Global free-memory endpoints
are **not** a global peak estimate. CPU fakes test API options, isolation and
failure handling; they cannot certify HF internal state or CUDA compatibility.

Before any GPU submission: independently acquire/pin/hash the candidate, freeze
software/bundle, pass both exact mount simulations and project Kaggle preflight,
then measure actual tensor execution. Predeclare a cache-bypassed A→B→A versus
fresh-A probe (fixed synthetic guard inputs) so the guard result cache cannot
fake statelessness. Record mismatches/invalid outputs, no semantic retries.
Next measure concurrent agent/guard residency, context stress, first/warm request
latency and cancellation cleanup. Only then consider grouped Dev guard quality.
No real-model success, real statelessness or end-to-end GPU memory fit is claimed.

Candidate evidence and source limitations:
[research note](../../knowledge/guard_model_preflight_evidence.md).
