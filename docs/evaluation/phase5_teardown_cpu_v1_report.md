# Phase 5 — post-serve teardown CPU controls

2026-09-17. [Protocol](../architecture/phase5_teardown_probe_v1_contract.md).
This is a synthetic lifecycle experiment, not a rerun or repair of the four
constrained GPU tasks. Phase 5 acceptance remains 4/7 ≈ 57%.

## Results

[Frozen control receipt](../../experiments/manifests/phase5_teardown_cpu_close01.json):
18 fresh spawned workers, six fixed conditions × three repeats, two unchanged
public responses per worker. All 18 workers reaped; two read-only audits are
byte-identical. Serial nonoverlap checked separately, 19 raw files rehashed,
31 source/evidence files scanned with zero credential-value matches.

| Injected mechanism | Repeats | Exit | Serve returned | Mean close (s) |
|---|---:|---|---:|---:|
| Fast process finalizer | 3 | GRACEFUL | 3/3 | 0.034 |
| 0.25s process finalizer | 3 | GRACEFUL | 3/3 | 0.288 |
| Blocked process finalizer | 3 | TERMINATE | 3/3 | 2.004 |
| Blocked finalizer, SIGTERM ignored | 3 | KILL | 3/3 | 2.207 |
| Blocked backend destructor | 3 | TERMINATE | 0/3 | 2.005 |
| Live non-daemon thread | 3 | TERMINATE | 3/3 | 2.005 |

Forced outcomes are predeclared positive fault controls, not failures discarded
to improve a result. Production graceful budget remains 2s. Only the CPU control
factory injects delays or signal behavior; frozen transport/native factories are
unchanged. Finalizer entry follows serve return in this measured interpreter;
thread-block controls finish the finalizer but not the thread.

## Interpretation and limits

Existing GPU telemetry (STOP received + serve returned + TERMINATE) is consistent
with more than one post-serve mechanism. These CPU controls demonstrate that the
old two markers do **not** identify the native cause. They do not prove that the
GPU failure is a Python finalizer, a thread, a CUDA cleanup or a library defect.
Destructor-only blocking produces a different marker pattern in this harness.

Measured environment is CPython 3.11.0/Darwin/x86_64, not Kaggle. Interpreter
bootstrap/exit-function source hashes and platform identity are recorded; timings
are descriptive and cannot select a production GPU deadline. No model weights,
GPU, network, benchmark Test/private GT or new Kaggle submission were used.

## Implementation, QA and provenance

New isolated probe, strict event/identity auditor and run/audit CLIs. Tests cover
real spawned workers, fixed ordering/receipt creation, source/config/PID/sequence
binding, timestamp ordering, malformed identities, unknown modes, fresh-output
requirements and existing shutdown regression behavior.
[Final QA receipt](../../experiments/manifests/phase5_teardown_cpu_qa01.json)
records **623 focused tests / 44.37s + 133 integration tests / 125.28s passed**,
setup/Ruff/mypy450 and knowledge/diff checks. The 172 constrained GPU, 142 earlier CPU, 86 tokenizer/native CPU and 175
baseline source pins remain unchanged. Full pytest excludes sealed Test-authoring
fixtures. This is precommit working-tree QA bound to exact source hashes plus
Git base `27626b1`, not a new native release claim.

Retained raw: `results/phase5_teardown_cpu_controls02`; independent audits:
`results/phase5_teardown_cpu_audit01.json` and `..._audit02.json`.
Preparation01 stopped because its case directory was not created before the
first receipt write; its identity is retained and excluded. Added an orchestrator
regression for this defect. No model inference or semantic retry occurred.

Revalidation on 2026-09-20: 56 source/QA-log pins and all 19 raw pins still match.
The new read-only audit `results/phase5_teardown_cpu_audit_20260920_01.json` is
byte-identical to audit01. Knowledge navigation plus teardown unit/integration
selection passes 50 tests (11.24s); setup/Ruff/mypy450/knowledge/diff also pass.
This revalidation does not replace the original receipts or rerun inference.

## Next gate

Design opt-in native process-exit instrumentation under a separate protocol:
post-serve entry, process finalizer entry/return, relevant non-daemon thread
counts/exit milestones, PID/monotonic ordering, failure/partial marker retention.
Do not log arbitrary thread names, payloads, secrets or hidden model reasoning.
Check that instrumentation itself does not change factory ownership/cleanup,
transport, signal handling or model outputs. Authenticate exact package before
a bounded native diagnostic; do not resubmit constrained GPU v1 or adopt a larger
deadline from these CPU controls. Representative guard quality/utility and final
DoD mapping remain separate unfinished Phase 5 work.
