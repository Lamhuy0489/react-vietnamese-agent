# Phase 5 — native observed-shutdown wiring v2

2026-09-14. Bounded CPU preparation for native execution, not a Kaggle release.

- A new native composition constructs `ShutdownPair` directly with pinned
  Qwen agent/guard identities and `ShutdownPairConfig`. Keep native factories,
  progress/policy/attention wrapper order, path isolation and lazy loading.
  Never replace private workers in a legacy pair. Agent-only retains the same
  native agent factory stack with typed `AgentWorkerConfig` and runtime v3.
- Versioned probe v2 uses runtime/auditor v3 and records separate startup/call
  deadlines. Retain the public calculator fixture only as a CPU wiring/control
  trajectory; this change does not authorize rerunning its old semantic result.
  A future GPU diagnostic needs predeclared lifecycle/guard-path objectives.
- Checkpoint identity binds profile, model/execution config and public inputs;
  resume skips completed immutable levels and refuses partial/changed attempts.
  No automatic semantic retry or outputs mixed across protocol identities.
- Native joined auditor v2 retains native load/policy/attention checks, requires
  the new probe/config identity and reports observed graceful exits separately
  from recovered memory and artifact integrity. Partial native calls remain
  explicitly unverified, never promoted to successful joins.

CPU acceptance: factory topology/laziness/pickle and fail-before-allocation
negatives; seven real-spawn synthetic levels and immutable/missing-only resume;
checkpoint identity mutations; native-shaped audit controls labelled as mocked
at the checkpoint boundary. Full quality checks and source/raw/data hashes.

No model load/GPU submission/Test or private-ground-truth parsing here. Existing
model, policy, prompt, datasets and all frozen source/receipts remain unchanged.
Exact archive/expanded package, release auditor/remote authentication, new GPU
diagnostic, grouped Dev quality and Phase 5 freeze remain separate open work.
