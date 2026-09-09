# Budgeted agent HF loader — 2026-09-09

Owner authorized continuing after the Kaggle mount diagnostic. New
[contract](../docs/architecture/phase5_agent_hf_v1_contract.md) and decision-log entry
separate runtime admission from the unchanged full-inventory README rejection.
All large weights remain on Kaggle; no local GPU or storage expansion requested.

## Implemented

- Live publisher-inventory SHA pin, full streamed file hashes, strict native
  geometry and exact339parameter index/header coverage before torch imports.
  Only the recorded6005byte README exception is allowed, never another runtime
  mismatch. BF16/F16 safetensors headers have bounded JSON, exact shape/byte
  offsets, no gaps/overlaps/duplicate keys or path traversal. Rehash after load.
- Separate dedicated-process agent backend with 12/7GiB allocator caps before
  loading, fixed20/8layer map, no offload/remote code, exact FP16 loaded tensor
  coverage and per-device metrics. Guard stays in its own process, loaded later.
- Fresh greedy512/seed42/dynamic cache, batch1 and rendered input1–4096 without
  truncation. Request failures retire, no semantic retry; logs exclude text.
- Native Qwen2Config adds rope_scaling=None. Only inert None defaults are
  normalized after load; raw authenticated config is still validated strictly.
  All28 native layer_types, when present, must be full_attention. Regression tests
  cover None admission and active config rejection; no frozen validator changed.

87new tests pass (43runtime-input +44adapter), synthetic tiny weights and CPU
CUDA/transformers fakes only. Ruff/setup and mypy221sourcefiles pass. Full final
suite is pending; earlier run started before the native-default adjustment and
must not be selected as final-source QA. `verify_phase5_agent_loader.py` preflight01
recomputes saved scan admission and7,615,616,512parameter arithmetic;134frozen
source hashes and hash-only Test seals unchanged. Saved receipt is not a live
loading permit. No real header scan, model load, GPU or new Kaggle submission.

## Next

Freeze source and retain clean-source reproductions after final QA. Then prepare
an explicit combined-process residency/context/cancellation protocol and worker
bundle, pin dependency image, simulate both archive/expanded runtime layouts with
all eight tools and21Dummy/resume. Check live quota and private inputs before a
new GPU job. Agent must be owned by a supervised process: this synchronous
adapter alone has no hard timeout, kill/reap or real VRAM recovery evidence.

Packaging entry points inspected: `scripts/prepare_phase5_guard_cancellation_v1.py`
and `notebooks/kaggle/guard_cancellation_kernel_v1.py` already demonstrate exact
archive/expanded/PAX handling, frozen Dataset verification and isolated Dummy
resume. Reuse their bounded approach in a new version; do not edit frozen files
or rerun the old cancellation/classification jobs. New overlay must include the
agent loader/runtime-input modules, mount scanner/audit dependency, placement,
publisher inventory and the future supervisor/probe, with explicit file hashes.

CPU mocks do not establish native HF/CUDA compatibility, allocator-wide/global
peak bounds, combined fit, guard quality, throughput or benchmark security.
Phase5 remains open: combined GPU, grouped Dev/guard model decision, general A4
scope and final entitlements. No Phase6/7 or held-out tuning.
