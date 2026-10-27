# Phase 5 — restart and host recovery correction, 2026-09-29

## Remote restart verified

The owner requested restarting both private inference notebooks. The previous
status observation was agent CANCEL_ACKNOWLEDGED and guard COMPLETE; the old
cached endpoint failed DNS resolution. The new package is
`build/kaggle/structured_pair_release03a_20260929`, using unchanged worker
source commit `728821ea761b3994eb40ebba91ab8238e4667f82` and new session/discovery
identities. Four archive/expanded role preflights passed before submission.

| Role | Actual notebook | Submitted version | Observed status |
|---|---|---|---|
| Qwen3-8B task agent | [buiquocviet/react-vn-qwen3-agent-api-v1](https://www.kaggle.com/code/buiquocviet/react-vn-qwen3-agent-api-v1) | 7 | RUNNING; authenticated health READY |
| Llama3.2-3B-Instruct guard | [huylmhuhu/react-vn-llama3-guard-api-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-llama3-guard-api-v1) | 5 | RUNNING; authenticated health READY |

Both pulled scripts match the generated scripts byte-for-byte and the remote
metadata confirms private visibility. No Dataset is mounted. The observation
was recorded at 06:40:16 UTC in `restart_verified.json` in that package. Version
numbers are the actual push receipts, not inferred increments from v2; this
audit does not account for the intervening remote versions. Fresh health is
still required before future inference. API keys and endpoints remain only in
private ignored local configuration. No experiment request was sent in this
restart audit; notebook model loading/warmup is separate from benchmark work.

## Host lifecycle defects reproduced and corrected

Scope: the existing, undeployed request-worker v3 host journal candidate. No
security policy, task-agent runtime, model prompt or notebook source changed.
Before editing, all five hashes from `request_worker_host_v1_cpu.json` were
verified and the corresponding bytes were preserved under
`build/evaluation/request_worker_host_v1_before_recovery_fix/`. The old manifest
remains historical and must be checked against that snapshot, not the corrected
working-tree journal. The old v1 structured API journal is unchanged.

Six new regression cases failed before the fix, demonstrating four defects:

1. A lost response blocked the same request ID but allowed a different ID/task
   to POST into the same worker scope. Admission now blocks any new POST while
   an unresolved record exists.
2. Ordinary completions did not require the same CUDA-quiescence and terminal
   outcome evidence as recovery. Both now use the existing terminal verifier.
3. A successful explicit recovery remained unreadable because the old uncertain
   record was checked before the separate recovery record. Recovery now permits
   reading the in-memory result without another POST, preserving the old record.
4. A recovered result could differ from the result promised by the status GET.
   Recovery now binds state, HTTP status and result hash across GET and POST,
   and also checks any previously saved completion/recovery envelope hash.

Two additional passing controls confirm that resolved delivery permits the next
task without overwriting earlier evidence, and a host restart cannot accept a
different cached result from the previously delivered result. The POST in
`recover_cached` retrieves the identical cached request; it does not authorize
new generation or semantic retries. This assumes the authenticated worker
honors its immutable request cache, as stated in the v3 contract.

## Verification and limits

- Eight new regression cases pass after the fix.
- Host/journal/lifecycle/reconciliation/quiescent controls: 64 passed.
- HTTP v3 controls including loopback cancellation/concurrency: 12 passed.
- Total focused verification: 76 passed. Setup, full Ruff and mypy for
  `src scripts` plus the two host test files pass (610 files).
- Full repository pytest was not repeated; its prior interrupted run and
  historical frozen-pin failures remain documented in the handoff. This report
  makes no full-suite-pass claim.
- CPU fake engines do not prove native GPU quiescence. The restarted notebooks
  still serve structured API v1 and do not expose v3 request status/cancel.
- No Test/private ground truth access, semantic retry or Phase 5 acceptance.

Next concrete implementation is the existing v3 notebook entrypoint, encrypted
discovery, and bounded lifetime shutdown with exact package QA. A predeclared
native lifecycle run requires that implementation and a source freeze first.
The already-completed Dev runs remain immutable and are not restarted simply
because the inference notebooks have new versions.
