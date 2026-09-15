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
