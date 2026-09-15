# Observer native v2 — separately identified synthetic diagnostic

2026-09-15. Scope is observability, not a retry or replacement of the112-task
Dev baseline and not a guard-quality experiment. No Test/private ground truth.

## Frozen diagnostic schedule and interpretation

Four fresh tasks in order: `CALC_A2`, `CALC_A6`, `DOC_A2`, `DOC_A6`. CALC asks
the calculator for17+25; DOC asks doc_read for public CDOC_034. The agent must
choose its actions itself in HF mode. New diagnostic task identities/instructions
are separate from the benchmark. Use the existing runtime v8, fixed generation,
Qwen7B agent/Qwen1.5B guard identities and observed-shutdown pair config.
No automatic output repair, prompt change, deadline change or semantic retry.

CPU `stub` has two explicitly separate conditions: `valid` and `trailing_comma`.
Each sends one scripted public tool action, then a public final answer. Valid
guard returns SAFE JSON (expected2 agent/2guard calls and PRE/POST per task).
Malformed guard returns a fixed JSON trailing comma (expected1 agent/1guard
response followed by retirement and POST BACKEND_FAILURE). These conditions are
synthetic test fixtures, never substituted for native model output. HF accepts
only `valid` as the condition identifier; it does not guarantee valid output.

Native response counts are observations, not guaranteed expected success. A
four-task terminal schedule without guard calls is still missing diagnostic
coverage. Record completed/error, PRE/POST, valid/malformed response counts and
lifecycle/recovery separately. Never assert utility or Phase5 acceptance from
terminal counts. Preserve every terminal result without selecting better retries.

## Interfaces and integrity

`native_guard_diagnostics_v2.native_pair(..., witness=Path)` lazily composes
unchanged HF/attention/policy factories with worker observer v2 and host-witness
DiagnosticPair. Witness lives in an existing task directory outside all fresh
native/attention/policy roots and model inputs. Native metrics root is created
only after path validation. No private worker factory replacement.

`guard_observer_probe_v2.run` binds source commit, backend/condition, schedule,
instructions/catalog/config/generation/security, environment hashes and native
inventory/snapshot hashes. One fresh pair per task. Resume re-audits every saved
checkpoint and runs only wholly missing tasks; partial attempts or unrecovered
tasks stop continuation. Changed identities and extra task directories reject.
Checkpoint hashes include runtime, worker diagnostic, host witness, memory
observations and the repeatable three-way join. Semantic errors stay terminal.

The CLI defaults to synthetic CPU. HF needs explicit model mount/snapshot and
two-T4 CUDA tensor preflight; no implicit network. CPU packaging must use fresh
offline venvs, exact archive/expanded source manifests, project-only PYTHONPATH,
eight tools,21clean public Dummy tasks, all4diagnostic tasks and missing-only
resume in both conditions. No tests/credentials/oracle/Test payload in package.

Acceptance of this milestone is CPU composition/checkpoint/package evidence,
not native submission approval or native library execution. Before GPU: freeze
the actual notebook launcher, native source/metrics audit, exact package receipt,
model/Dataset versions and quota. Keep the existing worker and175pins unchanged.

## Preflight correction, 2026-09-15

Native metrics directory creation occurs after the lazy factory validates fresh
roots and before worker start. A CPU regression exercises the actual HF branch
through factory validation and stops before weights load. All retained tasks
are audited before any missing task starts. New identities additionally bind
six rollout source file hashes; changed source cannot resume old checkpoints.
The original `cpu01` artifacts predate these pins: their `source_commit` is the
base HEAD during development, not proof that HEAD contained the working source.
Historical CPU audits remain available with that limitation explicitly reported.
CPU audit CLI requires `--source-commit` for the recorded run rather than using
the repository's current HEAD. HF runs need a separate native evidence audit.

## Native launcher and audit, 2026-09-15

`observer_native_kernel_v2.py` embeds the committed archive and bootstrap with
SHA-256 checks, uses the existing private guard Dataset v1 and agent mount,
collects tokenizer metadata, executes the four-task HF runner once, then writes
`native_audit.json`. Requested handle is `huylmhuhu/react-vn-observer-native-v2`,
private/offline with the previously pinned two-T4 image, timeout14400seconds.
`observer_bootstrap.json` records the actual source/Dataset/snapshot/wheel pins.

`observer_native_audit_v2.audit` verifies full schedule/checkpoints and pins,
model-load records, tokenizer/publisher admission, role PID/policy/attention,
native time bounded by worker time, and v2 worker/host response joins. It records
all terminal statuses, tool-call counts, cleanup methods and GPU recovery.
Transport failures exclude unjoined generation from timing denominators; zero
guard/tool calls remain visible. The verdict concerns artifact consistency;
`source_authenticated=false` until an external release audit matches downloaded
version/source/bootstrap to the submitted package. Quality/Phase5 flags stay false.

CPU tests use explicitly mocked evidence boundaries; load/policy/timing helpers
are additionally checked against immutable historical native logs. Those logs
cannot validate the new host witness. Native v2 evidence requires the new run.
Preflight03 must use the rendered launcher's embedded source in both mount
layouts, import the native audit CLI, and rerun the packaged CPU conditions.
