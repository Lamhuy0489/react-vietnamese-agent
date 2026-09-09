# Phase 5 model-pair lifecycle v1

Engineering supervisor only, not policy/runtime integration, model selection,
GPU fit, benchmark performance or Phase5 acceptance. Preserve all prior source,
including WarmGuardBackend and the failed graceful guard cleanup measurements.
CPU tests spawn tiny synthetic backends; no local model download or Test payloads.

## Ownership and sequence

One task owner owns two sibling spawn workers via the existing bounded warm
transport. Workers must not spawn child processes or external services; a pair
is not reusable across tasks. Neither model loads in the parent. The adapter
retains exactly one backend per worker and accepts a reserved readiness command
which returns a fixed ACK without calling model.generate. This technical command
is never sent to a model. It cannot be passed through the public generation API.

Start agent and verify expected model/revision first; only then start guard.
Accept user generation only after both ACKs. The agent's live runtime identity
must equal the explicit host-supplied expected revision; a saved scan never
replaces live authentication in AgentHFBackend. Guard factory remains unchanged.
Agent loads with12/7GiB process caps and explicit20/8layer placement; guard is
separate on device1 with5GiB cap. Verify both workers still alive before and
after each call. No inference calls are concurrent or shared between pairs.

Agent cold startup includes two full mount hashes, header validation and loading:
1200s ceiling. Guard cold startup120s, subsequent agent calls180s and guard calls
120s. Each request deadline includes parent dispatch, serialization, worker
start when applicable and transport validation; cleanup is separately bounded
by the inherited0.5s terminate/1s kill graces. Switching from cold to warm
timeout is explicit after ACK, same model identity; record both config hashes.
These are technical ceilings, not final benchmark latency settings. Test-only
deadline variants have distinct configuration hashes and are not GPU evidence.

## Fail-closed lifecycle

State: NEW -> STARTING -> READY -> CLOSED, or any operation failure -> FAILED.
No second start, retry, worker replacement, partial-ready generation or reuse
after close/failure. Reject concurrency and non-owning-PID use. Each guarded
operation cleans up on BaseException (including interruption), then rethrows;
do not retain arbitrary backend error text. On any model failure, identity drift
or dead sibling, close guard then agent and attempt both even if one cleanup
raises. Record pending cleanup honestly; retain worker handles so owner can
retry cleanup only, never generation. Pair context exit must run cleanup.

Use existing graceful/terminate/kill/reap behavior without loosening graces or
reinterpreting prior failures. Normal closure may require terminate. `closed`
alone is not reap evidence: inspect live handles and lifecycle `reaped` entries.
No claim that this handles owner SIGKILL, detached descendants or CUDA driver
failure. That requires separate evidence and must not be concealed by CPU tests.

## Evidence and next gate

Snapshot contains stage/status, PID, cold/warm execution identities, attempts,
cleanup lifecycle and sanitized error classes, never messages or raw responses.
The owner writes durable snapshots at boundaries; this supervisor does not write
unspecified files or change policy outputs. Underlying transport records request
hashes but not content. No hidden reasoning request/logging is added.

CPU acceptance: true spawn PIDs/load order, retained worker reuse, identity drift,
failure during either load or call, request overflow, timeout with siblings
resident, ignored SIGTERM escalation, abrupt worker death, owner/concurrency
checks and both-cleanup-attempted despite one error. Fresh pairs prove distinct
process ownership, not semantic model statelessness or real VRAM recovery.

Before Kaggle: declare exact residency/context/cancellation experiment and inputs,
provide process-owner cleanup in finally, persist state even on failure, prepare
and verify actual archive/expanded runtime bundle with8tools/21Dummy/resume,
freeze dependencies and source, check private inputs and quota. No submission
is authorized solely by a passing CPU supervisor suite.

## Durable residency probe implementation (synthetic rehearsal first)

`model_pair_probe_v1` records a manifest, baseline, both-ready snapshot, one
small-context agent call then one guard call, finally cleanup and six memory
samples. Only response hashes are recorded here; schema/quality and maximum
context are not acceptance criteria of this small technical probe. Guard uses
the unchanged prompt and one synthetic public notice, not the earlier A/B
classification diagnostic rerun. These new outputs are not a guard-selection test.

Memory observations must have exactly two ordered devices, nonnegative integer
free<=total counts and no extra fields. Require baseline-to-both-resident usage
of at least8GiB/device0 and6GiB/device1; this is a coarse sanity bound, not tensor
attribution. Six recovery samples1s apart, last three within256MiB of baseline
on both devices. Total capacity must agree. Parent observer establishes its
own CUDA context before baseline with a real tiny tensor operation on each GPU.
These thresholds apply only to a future HF invocation; synthetic rehearsal uses
explicitly fake memory and0s intervals. No real GPU evidence is produced now.

On errors, preserve partial files and sanitized error class, close both workers,
write final state and failure summary. No retry/resume; fresh output directory
required. The CLI in this milestone runs synthetic workers only and checks prior
source hashes/Test seals; HF CLI/packaging is a separate next gate. Interruptions
must still trigger finally-cleanup and persist a non-success summary.
