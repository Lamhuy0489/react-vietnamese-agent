# Combined pair cancellation v1

Phase5 engineering extension after the small-context pair GPU probe. Preserve
all frozen pair/transport/HF adapters and raw GPU outcomes. No semantic inference,
policy tuning, Test payload, full-repo upload, or local model weights.

## Fixed protocol

Three ordered trials, each a fresh pair: `agent_busy`, `guard_busy`,
`guard_ignore_term`. Load agent first then guard using unchanged ModelPair
readiness, identities, allocator budgets and cold/warm deadlines. Select only
the named busy role; the sibling remains resident and idle. An immutable host
command is consumed by a diagnostic backend wrapper, never sent to the model.
No backend.generate call occurs. In HF mode the busy worker performs small
256x256 FP16 matrix multiplications on its assigned devices (agent0+1, guard1).
This models a worker occupied with CUDA operations while weights stay resident;
it is not cancellation during native autoregressive generation.

Write a durable busy marker after actual operations, before the loop. In the
third case install SIGTERM ignore before the marker. Agent warm deadline180s,
guard120s; existing terminate0.5s/kill1s graces unchanged. A valid busy outcome
requires TimeoutError, the transport TIMEOUT attempt matching the marked PID,
both workers reaped, and no remaining handles. Ordinary busy cases must record
TERMINATE/-15; ignore-term must record KILL/-9. Sibling cleanup may be graceful
or forced; report the actual method without claiming graceful success.

Parent observer establishes stable CUDA context before all trials, performs
actual operations on both T4s, and keeps its baseline throughout the suite.
Before each trial require same device totals and free memory within256MiB of
the suite baseline. At both-ready require deltas >=8GiB/device0 and6GiB/device1.
After cleanup, six recovery samples with monotonic elapsed timestamps, nominal
1s interval, last3 within256MiB of that trial's baseline on both devices.
No recovery acceptance without both lifecycle reaps. Stop subsequent trials
after any failure, including baseline drift, load failure or recovery failure.
Retain partial files and sanitized exception class; interrupted runs write
non-success summaries and rethrow. Never retry a semantic or technical result
inside the suite. Cleanup-only retry stays the owner's responsibility if handles
cannot be reaped; do not pretend a failed cleanup completed.

## Current milestone and next gates

Implement protocol, diagnostic wrapper, durable suite and CPU-only rehearsal.
CPU tests use tiny synthetic backends and fake memory, shorter explicitly
recorded deadlines and zero sample interval. This does not certify GPU behavior.
No new GPU submission in this implementation milestone.

Before an eventual HF run: freeze exact HF factories and dependency/source
identity, verify model pins/private inputs/quota, exact archive and expanded/PAX
8tools/21Dummy/resume preflight, push source, then one private two-T4 execution.
Use the observed Docker digest from pair GPU v1 if supported and verify runtime
versions/operations; never weaken security checks to make a trial pass.

Maximum context is a separate next protocol: report exact tokenizer-rendered
input counts, truncation policy, observed generated length and KV/cache peaks.
A4096-token input with early EOS is not proof of4096+512-token allocation.
Any forced-length synthetic stress must be a versioned technical adapter,
not an unrecorded change to benchmark generation defaults. No such experiment
or GPU result is claimed by this cancellation implementation.
