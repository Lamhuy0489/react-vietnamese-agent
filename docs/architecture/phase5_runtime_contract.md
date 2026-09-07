# Phase 5 runtime v1 — A0/A1 integration milestone

New module only; frozen Phase 1/4/runtime/component bytes remain unchanged.
Inputs: public RuntimeTask, backend, registry, runtime/generation parameters,
host SourceCatalog, immutable SecurityConfig. This runner supports A0/A1 only;
A2–A6 and custom policy injection fail before creating outputs. The same loop,
parser, prompt, backend settings, tools and logging serve both supported levels.
RuntimeConfig.config_id remains A0 (baseline mechanics); SecurityConfig.level is
the authoritative defense level and is separately hash-bound in metadata.

## Pre/Post/Final behavior

Record every raw model output, parsed action, security-relevant argument field,
result and proposed final with Phase 4 conservative lineage. Each parsed action
gets a run-local proposal ID; denied proposals consume a step, not a tool call.
They never reach Broker, never receive a call ID and never fabricate ToolResult.
A source-dependent denial feedback artifact is generated from the action and
related source artifacts. Only a fixed, versioned POLICY_FEEDBACK envelope enters
model context, after the original assistant action. No evaluator facts, policy
reasoning or detector-normalized content enter prompts. If repeats exhaust the
ordinary step budget, terminal status is max_steps, not fabricated success.

Allowed proposals reach the unchanged ToolBroker, then RecordOnlyPostHook.
Source snapshots use host-native labels; result/context bytes remain raw. A1
scans only those source snapshots and keeps sticky rule signals; A0 skips it.
Detector errors are logged by class only (never exception text) and cause sticky
fail-closed external actions, while reads continue. Final is pass-through at A0/A1,
including after a detector error; full final security remains A6's responsibility.
PRE decisions aggregate rule-error evidence rather than silently swallowing errors.

The final sidecar records proposed and released artifacts separately by event;
they may share one artifact when byte-identical/pass-through. Do not claim A6
redaction or sensitive-value protection is implemented. No new model call is
made for a blocked tool; the next turn uses normal budget/decoding settings.

## Observability

`security_trace_v1` events: proposal, decision, denied, broker_result, rule_signal,
detector_error, proposed_final, released_final. Sequential/run/task/step identity,
proposal ID, artifact IDs and actual Broker call IDs link the traces. Existing
legacy tool trace records only calls that reached Broker; denominator for proposed
violations must come from security proposals, not only legacy calls. Parse-invalid
actions remain parser events and are not valid tool proposals. Run metadata records
proposal/denial/Broker counts, policy config/hash, rule version, feedback version,
source catalog and model/generation identity. Launcher adds Git/data/source hashes.

Phase 4 artifact/trace sidecars remain available. Only run UUID and timestamps
are ignored when comparing A0 observable traces. No hidden CoT is requested.
Default raw mode remains authoritative; optional normalized views are audit-only.

## Verification scope

20 frozen smoke trajectories: exact A0 messages/outcomes/legacy events vs Phase 4.
Synthetic end-to-end differential cases cover poisoned read -> email/webhook,
matched ordinary content, explicit user authorization, unknown/sensitivity labels,
zero-width raw preservation, failed reads, retries, repeated denials, parser and
model errors, final pass-through, fresh state and no sockets. A1 detector behavior
is frozen from the previous component milestone; no benchmark Dev/Test payload
inspection or rule tuning in this milestone. Public smoke is not held-out data.
The new QA audit asserts artifacts, actual model-parent sets, proposal/denial/call
order, metadata counters and serialized round-trips. A1 operational here means
CPU Replay end-to-end integration, not proven ASR or real-model efficacy.

Remaining: grouped Dev tune/validation protocol, fixed real guard identity and
bounded inference, A2 integration, A3–A6 policy and full Phase 5 acceptance.
