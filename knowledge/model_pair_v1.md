# Model-pair supervisor and durable rehearsal — 2026-09-09

[Contract](../docs/architecture/phase5_model_pair_v1_contract.md). Two sibling spawn
workers, parent never loads models. Compose frozen WarmGuardBackend; preserve
all earlier runtime/guard/agent source and GPU failure evidence. This is not
yet connected to the v5 policy runtime or a packaged HF/Kaggle job.

## Implemented

ModelPair owns task-local agent+guard: agent ACK first, then guard ACK, no real
generation for readiness. It switches explicit cold deadlines1200/120s to warm
180/120s only after ACK, with both config identities recorded. Same model IDs
and no worker replacement. Both must be alive before/after calls. Any failure
retires pair and attempts guard-then-agent cleanup, retaining unresolved handles
for cleanup-only retry. No inference after failure/close, concurrency or foreign
owner PID. Exceptions are sanitized by existing transport; snapshots contain
observable status/hashes/PIDs only. Normal cleanup may still require terminate.

37supervisor tests use real spawn workers and synthetic model factories. Cover
load order, startup failure, retained worker reuse, response/backend identity
drift, timeout with sibling alive, ignored SIGTERM requiringKILL/-9, abrupt
exit, oversized/reserved requests, state/owner/config/concurrency rejection,
interrupt cleanup and both cleanup attempts despite one failure.

19durable-probe tests cover manifest/partial/final snapshots, baseline/residency/
small-context calls/recovery, memory shape/error/leak rejection and interruption.
CUDA observer checked with fake tensor operation only. Existing runtime tools,
prompts/policies and benchmark data unchanged. No new model or GPU run.

`scripts/probe_phase5_model_pair.py` is deliberately synthetic-only. First rehearsal
`results/phase5_model_pair_v1_preflight01` completed with two synthetic calls and
both child processes reaped; fake memory recovered. Source subsequently changed
only for script line wrapping, so use a fresh final-source run for selection.
It verifies140prior source entries (134guard +6agent loader) and Test seals by
hash only. Raw PIDs/timing/lifecycle records are immutable and may differ across
reproductions; never call raw JSON byte-identical across actual spawn executions.

Full-suite final QA currently running with durable XML. Ruff/setup/mypy224files
pass. No Kaggle submission, local model download or pending account access.

## Next concrete step

Finish final QA, freeze/push supervisor and record selected clean-source CPU
rehearsal. Then add an explicitly identified HF entry point and exact source
overlay onto the frozen private guard Dataset plus pinned Qwen7B model mount.
Do not upload entire repo/credentials/private GT/Test/memory. Include model_pair,
probe, agent loader/runtime-input/mount scanner/audit, placement and publisher
inventory in the bounded overlay. Reuse archive/expanded/PAX handling in a new
version, run8tools/fault/21Dummy/resume on the actual packaged worker. Check quota
and source/private input hashes before GPU submission.

The implemented small-context residency probe does not cover maximum4096token
context, simultaneous generation, owner SIGKILL or detached descendants. Declare
any additional stress conditions before their GPU run; no semantic retries.
Group Dev/guard selection, broader A4/final entitlements and Phase5 acceptance
remain open. ModelPair is an engineering building block, not a new security gate
or full runtime integration.
