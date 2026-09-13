# Phase 5 — observed-shutdown pair/runtime v3 CPU evidence

Completed 2026-09-14 (Asia/Ho_Chi_Minh). Bounded synthetic CPU integration,
not native GPU lifecycle acceptance, model quality or Phase 5 closure.

## Selected result

Source `c4afb83f497d07067fa1a1d215548b8acd1ab426`. Full pytest: **2,704 passed,
one skipped in 670.56s**. Focused suite: 74 passed in 76.90s. Setup, Ruff,
mypy (335 source files) and knowledge-check passed. Optional native tqdm is
unavailable locally; this skip is not evidence of native dependency compatibility.
Measured subprocess wall intervals are 679.410s full and 77.514s focused;
these include process overhead and differ from pytest's reported durations.

[Selected receipt](../../experiments/manifests/phase5_pair_runtime_v3_cpu01.json)
SHA-256 `fc86feb846340e8e323e6f5fc842ab0f977f49463853decdbe2e3ba94aa183d8`.
Independent re-audit matched 468 source/646 raw hashes; 169 tracked data hashes
are unchanged. Parent standalone receipt still matches all 1,139 source/raw
entries. Raw root `results/phase5_pair_runtime_v3_cpu01` remains immutable and
untracked; the receipt is selected for Git. This is working-tree CPU QA, not a
claim that unrelated user edits were absent from the repository.

## Observed coverage

63 runtime receipts independently join host outcomes, requests, gate traces and
worker evidence. All workers are closed, with no pending handle and all recorded
exits reaped. Runtime lifecycle events: 91 GRACEFUL, 15 TERMINATE, four EXITED.
Fault injection accounts for forced/error exits; these counts are not a security
success rate or a prediction of native cleanup behavior.

Four additional pair teardown fixtures cover slow/hung teardown for each role:
six GRACEFUL and two TERMINATE events, all closed/reaped. Maximum recorded
cleanup in these four fixtures is 0.704544916s, a CPU fixture observation only.

The 74 focused tests cover seven levels and four terminal states, exact v7
observable/context parity, separate A0/A1 startup/call timeouts, both-role startup
and generation failure, post-response death, interrupted guard startup, guard
retirement, final entitlement, processing scope and external-sink veto. Mutation
controls reject PID/config/grace/ACK/protocol/lifecycle inconsistencies without
rewriting original raw artifacts.

## Change and limits

`ShutdownPair` directly constructs observed-shutdown workers for both roles;
A0/A1 use the same worker implementation but allocate no guard. New typed
execution configs separate start/call deadlines (default agent 1200s/180s),
with a separately hashed 2s normal-stop budget. Pair/runtime auditor v3 adds
PID/owner/sibling isolation, cold/warm identity and lifecycle joins while keeping
v2 host failure/trace checks. Frozen v1/v2/v7 implementations are unchanged.

No native model load, GPU submission, benchmark Dev run, Test/private-GT parsing,
prompt/policy tuning or dataset edits occurred. Hash-only sealed-data checks do
not expose payloads. The old calculator pilot remains zero tool/guard calls and
forced cleanup; it is not retried or reinterpreted by this result.

Next: versioned native factory composition, runner and joined/release auditor;
exact archive/expanded mount preflight; a new predeclared lifecycle/guard-path
diagnostic on Kaggle. Then grouped Dev guard quality, broader semantic coverage
and formal Phase 5 freeze. CPU stop acknowledgement does not prove CUDA memory
recovery or completion of native process finalizers.

[Contract](../architecture/phase5_pair_runtime_v3_contract.md) ·
[Next integration](../../knowledge/worker_shutdown_integration_next.md) ·
[Kaggle directory](../../knowledge/kaggle_resources.md).
