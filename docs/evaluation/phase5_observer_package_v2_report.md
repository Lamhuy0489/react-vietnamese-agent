# Phase 5 observer v2 package — CPU acceptance

2026-09-15. Source `ed0f6dbb6236c3ea6f12dee08d42982843dc05bd`.
[Selected evidence](../../experiments/manifests/phase5_observer_package_v2_cpu02.json),
[protocol](../architecture/phase5_observer_native_v2_contract.md).

## Outcome

The source archive contains140files;145source hashes including the builder and
contract were verified against the source commit. Both archive and nested
expanded mounts executed in fresh offline Python environments. No editable
installation or development working-directory import was available.

| Check, per mount layout | Result |
|---|---|
| Tool schemas and recovery adapter | 8 tools passed |
| Selected public clean Dummy tasks | 21/21 completed |
| Clean resume | Finished task hashes/identity unchanged; only missing task ran |
| Four observer tasks, valid scripted guard | 4 completed;8responses;4PRE/POST pairs |
| Four observer tasks, trailing-comma scripted guard | 4model_error;4PRE responses |
| Observer resume, both conditions | Completed output unchanged; only missing DOC_A6 ran |
| Worker cleanup and memory fixture | Reaped/closed; expected recovery observations |

The missing-task rehearsal creates a separate partial copy per condition; its
new DOC_A6 execution is a CPU reproducibility control. Counts in the table refer
to the four-task primary schedule per condition, not those additional controls.
All model backends and memory observations here are synthetic. No native weights
were loaded, and no GPU run occurred. Results establish packaging/runtime joins,
not semantic utility, guard accuracy or GPU shutdown/recovery.

Full preflight took67.31seconds. Independently rechecked706raw files across both
layouts and145source hashes; the175baseline worker pins still match. Relevant
source tests passed99/99 in41.02seconds; setup/Ruff/mypy405/knowledge checks passed.
The full repository test suite was not rerun; its historical frozen-worker QA
remains separate from these focused checks.

## Repairs and preserved evidence

1. Prior observer runner created `native/` before the HF factory required a
   fresh path. Directory creation now follows factory validation and precedes
   startup. A regression executes the actual HF factory and stops at the runtime
   boundary before weights load; CPU stub tests alone had missed this problem.
2. CPU audit no longer assumes the repository's current Git HEAD identifies an
   old run. The CLI takes `--source-commit`; validates scripted backend, exact
   task/terminal/stage coverage and recovered/reaped workers. New run identities
   include six rollout source hashes and resume checks all retained tasks first.
3. Preflight01 stopped because the clean runner's updated invocation timestamps
   were included in the unchanged-files comparison. Preflight02 checks task
   checkpoints and run identity, allowing the documented invocation summary to
   record the new call. The failed attempt remains on disk with its log/hash.

The original valid01/malformed01 probes are preserved and re-audited with the
explicit historical base commit. [Historical re-audit](../../experiments/manifests/phase5_guard_observer_probe_v2_historical_reaudit01.json)
sets `execution_source_pins_verified=false`: those identities predate the source
pins and record a base HEAD while working changes were uncommitted. Do not claim
that the old HEAD contained the observer probe code. New package evidence binds
the executed source to the committed archive.

## Artifact paths and next work

- Accepted archive/manifest/full receipt: `build/kaggle/phase5_observer_package_v2_preflight02/`.
- Logs and timing: `results/phase5_observer_package_v2_preflight02/`.
- Preserved first failure: same paths ending `preflight01`.
- Per-layout probe/audits: `cpu/{archive,expanded}/observer/` inside the accepted package.

Next implement the native evidence audit for this four-task schedule: bind
model-load inventory, tokenizer/publisher configuration, attention/request-policy
metrics, host/worker response joins, process lifecycle and real GPU observations.
Freeze a notebook launcher that executes the same packaged entrypoint and records
those sidecars, then verify account quota, Dataset/model mounts and submit under
the owner's existing authorization. Any added sources need a fresh package
identity/preflight; do not edit preflight02 in place.

The current package receipt has `native_submission_ready=false`. There is no new
Kaggle notebook URL/version to record yet. Phase5 acceptance remains4/7≈57%; the
remaining semantic/lifecycle/freeze gates need native evidence.
