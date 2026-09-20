# Exit milestones — paired runtime/runner v1

2026-09-20. Opt-in diagnostic composition, not production acceptance. Frozen
constrained/worker/observer sources are unchanged; no module-global patches.

## Boundaries

`ExitPairConfig` extends ShutdownPairConfig with an explicit observer field and
returns MilestoneConfig for both cold and warm deadlines. Existing deadline and
model values remain unchanged. `ExitPair` preserves DiagnosticPair witness and
ModelPair ownership/start/generate/cleanup semantics; its constructor privately
binds the frozen pair initializer to MilestoneBackend. No worker is constructed
and subsequently replaced. Snapshot schema stays model_pair_shutdown_v2; the
observer field changes config hashes and is admitted only by the new auditor.

Native factory composition privately binds the existing lazy builder to this
pair; guard factory topology/snapshot admission is retained. Synthetic factories
remain explicitly distinct from native factories. Native constructor tests are
mocked/lazy on the host and do not certify real model execution.

After runtime cleanup, write a fresh `execution/exit_milestones.json`, binding
task ID/instruction hash, owner, pair config hash and exact pair_runtime.json SHA.
For each role retain either reaped milestone slots or explicit unreaped status
without reading live slots. Unstarted workers must not invent markers. Never
overwrite sidecars or modify the baseline receipt. Failures propagate unchanged;
partial task directories are not auto-retried. No thread names or extra payloads.

Read-only join first inventories the tree (reject symlinks before reads), runs
existing constrained runtime/witness/constraint audits with only the typed config
admission rebound, then binds observer slots to the corresponding role lifecycle
PID, cold/warm identity and monotonic observation end. Exact sidecar fields only.
Missing/unreaped/invalid sidecars cannot qualify as completed evidence.
Native host audit binds all role markers to the structurally validated interpreter
identity recorded by the run, not the auditing host's OS/Python version. Remote
source/environment authentication remains a release-auditor gate; this binding
alone cannot authenticate a claimed interpreter. Run/resume still requires the
current worker environment to match its saved identity.

## Runner and acceptance

Separate four-task profile: CALC/DOC × A2/A6. Reuse frozen task/prompt/generation,
constrained guard policy and runtime mechanics. New identity pins observer,
pair/config, runner and join source bytes plus CPython exit-function hashes.
Checkpoint includes observer sidecar and joined evidence; resume is missing-only
after checking every retained task. Never resubmit an old native notebook.

CPU gate: four valid completions, four deliberately failed guard controls,
missing-only resume without rewriting retained errors, corruption/partial refusal
before spawning, startup failure evidence and pair isolation. Native factory
admission must remain lazy and globals unchanged. Existing frozen pins intact.
No local pretrained inference, Test/private GT or GPU. Record Git base plus exact
working-tree hashes; keep work local by default, not a commit per chat turn.

Next gate: native policy/timing/role audit integration and exact Kaggle package
rehearsal (archive + expanded, native interpreter) before any source freeze or
submission. CPU pairing alone is not a GPU diagnosis, quality score or Phase 5
acceptance. Grace2s remains fixed.
