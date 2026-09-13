# ModelPair security runtime v1

Task-owned integration of the existing ModelPair transport and runtime v7.
This is a CPU integration candidate pending native Kaggle validation.

`run_pair_task` accepts a fresh task, source catalog, unchanged A0 mechanics,
generation settings, registry factory, security configuration and either:

- A0/A1: an agent factory and explicit bounded agent execution settings;
- A2–A6: a NEW ModelPair with immutable agent/guard model identities and separate
  cold startup/warm call deadlines. No extra agent factory is permitted.

All components run in their existing locations: two sibling inference workers,
parent-owned role adapters, parent-owned security policy and Tool Broker. No
pair is transferred to a child and no third guard worker is created. READY
acknowledgements are stored separately from actual model-generation attempts.
The dedicated `guard_trace_pair_v1` schema preserves transport sequence numbers:
READY is sequence 1, inference starts at 2 with `cold_start=false`. It must not
be validated as `guard_trace_warm_v1`. Host role proposals are recorded separately
from worker attempts: a closed pair can reject a proposal before dispatch.
The joined auditor checks these counts, request identities, gate coverage,
cache evidence and worker cleanup rather than assuming every proposal was sent.
A0/A1 never construct a guard worker. Their single execution deadline is supplied
explicitly and currently applies to startup and calls; separate agent-only cold
and warm deadlines are not claimed by this version.

Runtime v7 retains A4 scope, A6 final entitlements, source tracking and all guard
fallback/cache behavior. A guard error retires the pair; further agent generation
terminates as model_error. Invalid guard JSON is not retried. No raw error string
enters the lifecycle receipt. No policy/evaluator or prompt changes occur.

The outer fresh output root contains `runtime/` traces and `pair_runtime.json`.
The latter is written on normal return, startup failure, inference failure and
cancellation. It binds task/security/catalog/generation/config identities and
records actual worker attempts, lifecycle exits, handles, timings and error class.
Cleanup always attempts all owned workers. The inner v7 loop closes the pair
before final metadata; consequently its measured runtime includes inner cleanup.
Outer cleanup time is recorded separately and must not be presented as total
worker cleanup latency. CPU tests assert reaped worker PIDs as well as flags.

Run identities are fresh and immutable. `verify_phase5_pair_runtime.py` saves
focused real-spawn artifacts plus full development QA, source/raw/data hashes
and prior repair integrity. Hash-only tracked data checks do not authorize
held-out payload parsing. Native model performance, GPU memory recovery,
production guard quality and Phase 5 freeze require further evidence.
