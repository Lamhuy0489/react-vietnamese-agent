# Independent ordinary A/B/A artifact audit v1

Phase 5 continuation after runner `44cf902`. Inputs are closed, immutable
ordinary-pair artifacts and public model metadata. New auditor modules and CLIs
do not alter the runner, policy/attention writers, supervisor or measured source.
No model load, tensor execution, prompt tuning, Test payload or private GT.

## Supervisor layer

Caller supplies expected full commit and backend; do not infer either from the
raw manifest. Reject mismatched source identity, incomplete/error/extra files,
duplicate/nonfinite JSON, symlinks and unexpected directories. Recompute the
manifest against frozen public A/B fixtures, PairConfig and decoding. Stub and
HF identities are distinct; both require the declared default deadlines.

Require one READY and three ordinary attempts per role, exactly one worker PID
per role and a distinct owner. Validate request/generation/execution hashes,
sequence, retention, one load, bounded timing and recognized final cleanup.
Compare every submitted/returned/ready snapshot with the appropriate prefix
of the closed supervisor ledger. Validate host/worker timing containment,
response SHA syntax, both-device residency, six ordered recovery records and
the final three residuals within the frozen tolerance. Recompute summaries.
Report repeated A mismatch as a measured observation, never reject it as a
semantic failure or choose a different attempt. Forced reap and graceful exit
remain separately reported. Source string agreement is not source authentication.

## Joined native layer

Require disjoint probe/policy/attention/publisher roots, pinned guard snapshot
content identity and exact publisher JSON hashes from prior upstream evidence.
Join the frozen request-policy auditor to each supervisor PID and three indexed
native metric calls. Authenticate the agent's admitted runtime-file list by
its content digest and bind both roles' generation metadata to the publisher.
Check fixed placement, allocator caps, load and request memory ordering,
global memory bounds and native-to-worker-to-host timing containment.
Report per-call input/output counts, native generation/call time, host time and
output tokens per generation second. Instrumentation overhead remains included.

Pad IDs are explicit caller expectations. Tokenizer reconstruction, source/
wheel/model execution authentication and remote wrapper/package checks remain
release-level requirements. Successful joined records are not proof of native
execution: `native_validated`, `source_authenticated`, tokenizer authentication
and Phase 5 acceptance remain false. Existing role-audit limitations are retained
inside the joined receipt rather than rewriting historical evidence.

Both CLIs write only a fresh output outside all raw inputs. The supervisor CLI
works on saved CPU rehearsals; native CLI requires all four roots plus snapshot,
expected commit and explicit pad IDs. Hash and directory inventories must be
unchanged before/after audit. Error/partial runs stay immutable and are rejected
by the completed-run auditor for separate investigation.

## Verification and next gate

Real spawned stub writer produces the supervisor fixture. HF-shaped fixtures
use explicitly synthetic model/config/tensor/memory values and real policy/
attention writers, plus public hash-bound metadata only. Mutation controls
cover missing/duplicate calls, swapped PIDs, prefixes, identity/config drift,
nonfinite times, cleanup/recovery, publisher/source list drift, role joins and
allocator limits. No GPU validity is inferred from these fixtures.

Next: tokenizer metadata admission and source-authenticated exact Kaggle package
preflight, followed by the authorized native repeated-request run. A0/A1 task
ownership, runtime A0–A6 parity/lifecycle and grouped Dev gates remain open.
