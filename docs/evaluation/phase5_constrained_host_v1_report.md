# Phase 5 — constrained host/cache/runtime integration

2026-09-16. Source `e04cd8d` (initial integration `d270830`).
[Contract](../architecture/phase5_constrained_host_v1_contract.md).
This is a bounded CPU integration milestone, not production guard acceptance.

## Implemented

- A task-local constrained guard role over the unchanged sibling transport.
  Native entry rejects ordinary/synthetic factories before startup; the synthetic
  entry is explicit and cannot silently substitute for native admission.
- Guard responses require exact worker receipts: PID/request index/model,
  request/generation/response hashes, decoding identity, ordered processors,
  token/callback counts and restored scopes. No parser repair or inference retry.
- Classifier cache uses decoding identity; a cache hit adds no IPC/model request.
  Before cache reuse, check host ownership, pair/factory/config identity, worker
  health and the full validated receipt tree, including empty directories/links.
  This does not remotely inspect a live model's configuration.
- Separate runtime bindings preserve the A2–A6 policy bodies, bare-JSON prompt,
  tool broker, parser and lifecycle. Metadata names the new execution/cache identity.
- Read-only auditor joins runtime classification, worker attempt, response sidecar,
  host witness and constraint receipts. It extends only the exact cache-key object
  during canonical encoding; saved traces and baseline module globals are unchanged.
- Errors rejected before dispatch get an explicit local admission record with
  zero new worker attempts. Failed/partial receipts remain evidence, never successful
  completion; inconsistent success evidence is rejected, not repaired.

## CPU evidence

37 new tests pass (20.89s in the targeted run): four spawned runtime cases
CALC/DOC × A2/A6, repeated read-only audits, cache reuse, worker failure and local
rejection, identity/config/factory/history/ownership/health drift, concurrency,
receipt mutation, unknown trees, symlinks and native-entry isolation.
The synthetic worker writes explicitly synthetic constraint receipts; these
tests are **not** evidence that Transformers or the pretrained guard executed.

Final [source-pinned QA](../../experiments/manifests/phase5_constrained_host_cpu_qa02.json):
**438 focused tests / 42.30s and 90 prior-runtime integration tests passed**.
Setup/Ruff/mypy 437/knowledge/diff checks passed. Frozen active CPU 142,
prior-native 86 and baseline 175 source pins remain unchanged. Full repository
pytest was not run because Test-assigned authoring fixtures must stay excluded.
Commands, source commit/hashes and log hashes are retained in the receipt;
raw logs are in `results/phase5_constrained_host_cpu_qa02`.
Pre-hardening [QA01](../../experiments/manifests/phase5_constrained_host_cpu_qa01.json)
under source `d270830` (436 tests / 43.47s) is preserved as history, not overwritten.
[Final integrity/secret scan](../../experiments/manifests/phase5_constrained_host_cpu_close01.json).

No new Kaggle submission, GPU use, pretrained inference, Test or private GT access.
Existing [native CPU v2 result](phase5_constrained_generate_cpu_v2_run.md) remains
separate tiny-model compatibility evidence. User Phase6–9/report edits untouched.

## Still required before GPU

Connect the new constraint join into the native release wrapper together with
request-policy, attention/cache-shape and HF-metric validation; implement the
candidate runner/checkpoint identity and exact offline archive/expanded package.
Freeze a new GPU protocol and authenticate source/mounts/quota before submission.
Do not rerun the old notebooks or treat this CPU harness as production quality.
Guard quality, benign utility, graceful lifecycle and formal freeze remain open;
Phase 5 is still 4/7 ≈ 57% acceptance groups.
