# Phase 5 — observed shutdown v2 CPU evidence

Completed 2026-09-14 (Asia/Ho_Chi_Minh). Standalone worker QA only; no native
model load, new GPU run, held-out payload parsing or Phase 5 acceptance.

## Result and reproducibility

Source `a45696bff6682d554a2d808ca5cb19d86f5bb8a3`. Full suite **2,630 passed,
one skipped in 581.50s**; focused 80 passed in 55.31s (34 new and 46 existing
warm-worker tests). Setup, Ruff, mypy (331 source files), knowledge-check passed.
The skip is the optional native tqdm dependency unavailable on the local machine.

[Selected CPU receipt](../../experiments/manifests/phase5_worker_shutdown_v2_cpu01.json)
SHA-256 `0f2b43d7472b6c62959b2bf6aa94bb9fec070f7d7ba34cf6bf1053ec7ce383df`.
Independent re-audit matched 462 source and 677 raw hashes; all 169 tracked
data hashes unchanged. The prior release CPU evidence also matched 3,317 entries.
Raw root `results/phase5_worker_shutdown_v2_cpu01` remains untracked/immutable;
the manifest is selected for Git. No pending QA or GPU process at this handoff.

## What was observed

Nine saved synthetic cases: eight v2 lifecycle events plus the unchanged v1
short-budget control. All workers were reaped; test assertions also checked
the absence of their PIDs from active multiprocessing children.

| Synthetic condition | Method / exit | Stop received | Serve returned |
|---|---|---|---|
| Normal teardown | GRACEFUL / 0 | yes | yes |
| 0.4s teardown with independent normal-stop budget | GRACEFUL / 0 | yes | yes |
| Hung teardown | TERMINATE / -15 | yes | no |
| Hung teardown ignoring SIGTERM | KILL / -9 | yes | no |
| Abrupt teardown exit 9 | EXITED / 9 | yes | no |
| Abrupt teardown exit 0 | EXITED / 0 | yes | no |
| Backend generation failure | TERMINATE / -15 in this run | no | yes |
| Generation timeout | TERMINATE / -15 | no | no |
| Frozen v1 with 0.05s stop/terminate budget, 0.4s teardown | TERMINATE / -15 | unobserved | unobserved |

Maximum recorded v2 cleanup in this focused run: 0.704631384 seconds.
These are CPU fixture timings, not production/native shutdown bounds or speed
measurements. Backend-error cancellation can race with a natural exit; its
required invariant is bounded reap without requesting a graceful wait.

The control demonstrates a known synthetic short-budget condition, not the
cause of the historical native v1 forced cleanup. An acknowledged stop or an
abrupt exit 0 alone must not be labelled GRACEFUL. Return from the service loop
does not establish CUDA memory recovery or completion of all process finalizers.

## Scope preserved and remaining work

The worker adds a separately identity-hashed normal-stop budget and observable
stop/serve-return timestamps while retaining v1 transport. AST parity tests
check the copied generate method except its observer entry and timestamp args.
Timeout/failure cancellation, ownership/idle locks, retirement and no-retry
semantics remain. Mutation tests reject inconsistent stop/return/exit records.

No frozen worker, ModelPair, runtime, model, policy, prompt or dataset was edited.
The worker is opt-in and **not integrated into native ModelPair/runtime yet**.
Next is versioned pair plus agent-only wiring and cross-receipt lifecycle
auditing, followed by exact package preflight and a separately identified native
diagnostic. Guard-path/quality coverage and Phase 5 freeze remain open.

[Contract](../architecture/phase5_worker_shutdown_v2_contract.md) ·
[Integration next](../../knowledge/worker_shutdown_integration_next.md) ·
[Kaggle resource directory](../../knowledge/kaggle_resources.md).
