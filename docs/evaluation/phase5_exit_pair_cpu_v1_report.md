# Phase 5 — paired exit observer and native audit wiring

2026-09-20. [Contract](../architecture/phase5_exit_pair_v1_contract.md).
This closes a CPU composition gate, not a native GPU diagnosis or Phase 5 acceptance.
Changes remain local/uncommitted under the owner's clarified commit cadence.

## Implemented

The opt-in ExitPair uses distinct cold/warm configuration identities while
inheriting existing witness, startup, generate and cleanup behavior. Its native
builder preserves the exact constrained guard factory topology and model/deadline
values. Construction is lazy and factories remain spawn-picklable. Frozen worker,
runtime and factory files are unchanged; no imported module globals are patched.

The runtime writes a separate `execution/exit_milestones.json` after cleanup,
binding task/instruction, owner, pair config, pair snapshot and SHA of the original
pair_runtime receipt. Role evidence records either reaped slots or explicit
unreaped status without reading live memory. Startup failures retain evidence;
never-started siblings have no invented markers. Incomplete cleanup cannot pass
the acceptance auditor.

The new read-only join checks role/PID/config/monotonic identity on top of existing
constrained runtime, host witness and worker-token audits. The native wrapper
retains policy/attention/token-count/timing checks and adds exit evidence. Native
wrapper tests are mocked composition checks, not native model execution proof.
Native audit binds the interpreter recorded in the run identity, not the host
Mac's Python/OS. The recorded identity is validated for schema/hash consistency;
remote authenticity still requires the future release auditor. Runtime resume
continues to require the current worker environment to match its saved identity.

The separate four-task runner reuses CALC/DOC × A2/A6, prompt, generation and
runtime mechanics. Checkpoints include milestone sidecars and the joined results.
Resume checks every existing checkpoint before starting missing tasks. Symlinks
are rejected before reading saved identity; corrupted or partial attempts remain
on disk and cannot trigger automatic retries.

## Saved CPU controls

[Closure receipt](../../experiments/manifests/phase5_exit_pair_cpu_close02.json).
Raw root: `results/phase5_exit_pair_cpu_controls02`.

| Condition | Terminal tasks | Reaped workers | Observed exits | Raw files |
|---|---|---:|---|---:|
| valid | 4 completed | 8 | 8 GRACEFUL | 101 |
| deliberate guard backend failure | 4 model_error | 8 | 4 GRACEFUL, 4 TERMINATE | 77 |

All selected workers' observed stages returned. Forced exits in the failure
condition remain cancellation evidence, not graceful success: completed markers
do not prove the process exited naturally. Controls01 had one partial thread
marker during immediate cancellation; this does not prove thread shutdown blocked.
Controls01/QA01/close01 are retained historical evidence, excluded from the
selected closure after fixing cross-environment interpreter binding. Controls02
uses the corrected sources; no model inference or semantic retry was involved.

Both complete-resume operations preserve all raw bytes. Independent audits before
and after resume are byte-identical for each condition. Missing-only resume and
retention of terminal failures are additionally exercised by integration tests.
31 execution-source pins bind each runner identity; Git base `5875bb7` alone does
not contain the new uncommitted code. There is no new model inference, Kaggle
submission, Test/private GT access or benchmark quality estimate.

Commands use `scripts/run_phase5_exit_pair_v1.py` (CPU-only CLI; optional
`--condition backend_failure` / `--resume`) and
`scripts/audit_phase5_exit_pair_v1.py` with explicit probe, condition, Git base and
fresh audit output. The library has a native path, but no released native CLI or
package is claimed yet.

## Verification and next gate

[QA receipt](../../experiments/manifests/phase5_exit_pair_cpu_qa02.json) records
commands, exact source/log hashes and frozen-pin checks. Full pytest excludes
sealed Test-authoring fixtures. Local results are not backed up off-machine.
Final QA02: 689 focused tests (50.98s), 180 integration tests (180.37s),
setup/Ruff/mypy462/knowledge/diff all pass. 54 new tests cover pair identity,
native lazy topology, cross-host audit, startup failure, corruption and resume.
The previous 172/142/86/175 frozen-source pin sets and prior milestone sources
remain unchanged. Neither this work nor the selected local manifests have been
committed/pushed; the source identity is the exact working tree plus Git base.

Next: prepare the exact native notebook/package and its release auditor for this
new profile; rehearse archive and expanded layouts and native interpreter hashes.
Only when this larger unit is ready may source freeze require a commit. No routine
commit/push after a chat turn, no amend of previous experiment sources. Native
quality, benign utility, lifecycle diagnosis and formal freeze remain open;
Phase 5 is still 4/7 groups (approximately 57%).
