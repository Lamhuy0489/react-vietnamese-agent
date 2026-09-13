# Phase 5 — ModelPair/runtime CPU evidence

Date: 2026-09-13. CPU02 bounded CPU integration and full repository QA passed.

The parent-owned role adapter connects the existing ModelPair to the validated
runtime v7 without moving the pair into a child process. A0/A1 allocate one
agent worker; A2–A6 allocate two sibling workers. All tool decisions, guard
parsing/cache retirement, A4 scope and A6 final entitlements remain in the
runtime. The outer runner records worker lifecycle even on startup failures
or cancellation before the runtime begins.

## Focused measured results

- 52 tests passed in 58.03 seconds using actual spawned processes and synthetic
  backends; no local model weights or GPU inference.
- 7 exact observable/context parity comparisons against v7 with the same
  synthetic backend identity, inputs and generation config.
- 28 level/terminal cases: A0–A6 × completed/parse_failure/max_steps/model_error.
- Additional cases cover load failures, generation timeout, cancellation between
  startup and execution, invalid guard output, existing output rejection,
  actual DB final release/redaction, cumulative scope denial and guard veto.
- Four deliberate corruption tests cover schema, request, READY and host count.
- 51 task receipts retained and independently joined with runtime/worker traces;
  the fresh-output rejection creates no task receipt.
- 51 agent startup attempts and 40 guard startup attempts, separately recorded
  from 86 agent and 68 guard post-startup attempts. Counts include deliberate
  failure conditions and must not be reported as successful model calls.
- 80 GRACEFUL and 11 TERMINATE worker exits; zero unclosed handles in receipts.
  Tests also inspect active child PIDs. CPU cleanup success does not establish
  native GPU memory/IPC recovery.

## Receipt and verification

Raw outputs: `results/phase5_pair_runtime_v1_cpu02/`.
Validator: `scripts/verify_phase5_pair_runtime.py`. It captures QA logs, JUnit,
runtime traces, pair task receipts, source hashes, tracked data hashes and an
independent audit of the preceding repair receipt.

Full pytest: **2,496 passed, one skipped in 477.43s**; the skip is native tqdm
unavailable locally. Setup, Ruff, mypy (317 source files) and knowledge checks
passed. Independent re-audit found 441 source/530 raw hashes matching and all
169 tracked data hashes unchanged; all 51 joined task audits passed.

[CPU02 manifest](../../experiments/manifests/phase5_pair_runtime_v1_cpu02.json)
SHA-256: `1bc819d51f47e90f2fb35ad904087626cbb958ea8665b250a848ec335009312e`.
This is working-tree CPU QA anchored to parent `819af7a`, not a clean-source
native release. The source inventory identifies the actual tested bytes.

## Historical CPU01 deviation

CPU01 passed 2,492 tests/one skip in 588.87 seconds; its code snapshot is
`819af7a`. Independent audit then found the warm-only trace schema incompatible
with pair READY sequence 1. Preserve CPU01 raw outputs and receipt unchanged,
but do not select it as acceptance evidence. CPU02 has the dedicated pair trace
schema and a host ledger distinguishing rejected proposals from transport
attempts. No policy, model, prompt, decoding or benchmark was changed.

## Remaining scope

Exact native Kaggle package/mount validation, native agent-only attention/policy
parity, GPU runtime/memory/cleanup, production guard quality/grouped Dev and
Phase 5 freeze. No new benchmark Dev/Test inference has run. Runtime elapsed
includes the v7 inner cleanup; outer cleanup time is not total cleanup latency.
Failed startup currently uses zero as the outer startup-completion sentinel,
not zero measured load cost; failed-attempt elapsed remains in worker evidence.
Post-response sibling failure requires additional fault coverage and an auditor
that distinguishes pair acceptance from the worker response before native use.
See [contract](../architecture/phase5_pair_runtime_contract.md) and
[native follow-up](../../knowledge/phase5_pair_runtime_kaggle_next.md).
