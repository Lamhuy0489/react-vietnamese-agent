# Phase 4 acceptance report

**Accepted 2026-09-07 under the existing owner self-review waiver.**
Source `be7f8b5`; [selected closure receipt](../../experiments/manifests/phase4_closure_v1_validation01.json).
All 12 DoD gates below pass on the bounded Phase 4 scope. Scope and measurement budgets
were fixed in the [protocol](phase4_closure_protocol.md); the
[design index](phase4_design.md) maps the plan deliverables to implementation.

## Acceptance matrix

| Plan gate | Executable evidence |
| --- | --- |
| DoD-1 raw preservation | Golden normalization tests, 1,650 Dev primitive checks; frozen raw hashes rechecked |
| DoD-2 deterministic normalization | Repeated outputs, operation/cache hashes in `test_phase4_primitives.py` and primitive receipt |
| DoD-3 idempotence | Golden corpus and all 550 Dev texts across three profiles |
| DoD-4 artifact completeness | Runtime parity validator compares model/final artifacts and actual contexts; source/result/argument artifacts serialized and checked |
| DoD-5 provenance completeness | Validator rejects unexplained roots; deep Dev audit checks every source ancestor of final and sensitive DB ancestors of five sink fields |
| DoD-6 DAG integrity | Store parent validation, transitive closure, forged-parent and serialization tamper tests |
| DoD-7 independent labels | Cartesian sensitivity/trust tests plus host defaults, collection joins and S2/UNTRUSTED sink propagation |
| DoD-8 A0 preservation | Prior 20 smoke pairs plus 45 fresh clean/deep Dev pairs: exact messages, actions, tool results, final and terminal behavior |
| DoD-9 hook readiness | Pre/Post/Final counts, pass-through parity, denial/mutation rejection tests; no defense enabled |
| DoD-10 Dev integration | 21 fixed clean Dev and 24 paired deep Dev trajectories complete; 90 fresh Replay runs |
| DoD-11 frozen Test | Clean/adversarial seals and prior source/raw hashes checked before/after; new QA rejects Test parsing |
| DoD-12 reproducibility | Git/source/profile/schema/config/seed/input hashes, raw file hashes, matching preflight stable summary and quality logs required by closure launcher |

Primitive and runtime evidence remain in
[primitive receipt](../../experiments/manifests/phase4_primitives_v1_validation01.json)
and [runtime receipt](../../experiments/manifests/phase4_runtime_v1_validation01.json).
The closure launcher revalidates 497 prior hash entries; it does not modify
their source or outputs. Tests live in `tests/unit/test_phase4_primitives.py`
and `tests/integration/test_phase4_{dev_primitives,runtime,closure}.py`.

## Selected reproduction results

Selected raw output: `results/phase4_closure_v1_validation01` (ignored).
The selected run matches the Dev stable summary from the local preflight
`results/phase4_closure_v1_preflight01.json`. All 153 source and 1,625 raw file
hashes were revalidated after completion. Source was clean and committed before
execution; no old source/data/experiment file was modified. This run adds
532 Replay executions: 90 Dev + 440 smoke measurement + two stress; quality
tests also execute their own fixtures and are not counted as measured samples.
All 244 tests pass (20 new); setup, Ruff, mypy on 160 source files and knowledge
validation pass. Dev audit: 45 paired conditions, including 24 deep trajectories
with 152 source snapshots, 12 search envelopes and 120 sink fields. All source
snapshots reach final lineage; sink fields retain S2/UNTRUSTED. Clean Dev private
reference steps/faults are QA-only, never runtime or prompt metadata.

Seven timing repeats after warm-up and three separate memory repeats produced
440 smoke Replay executions. Added runtime median 5.539 ms, p95 11.749 ms;
median paired task ratio 1.913. Instrumented max traced peak 527,301 bytes;
both predeclared guards pass (<100 ms p95 added, <32 MiB traced peak).
Instrumented median log bytes 57,446 versus 3,589 legacy. These are CPU Replay
diagnostics on macOS 12.7.5 x86_64/Python 3.11.0, not LLM/GPU performance.

The separate 64 KiB/eight-read stress pair produced 4,111,390 instrumented log
bytes versus 533,821 legacy, and 21,603,744 traced peak bytes versus 1,686,599.
Its timings include allocation tracing and must not be compared to untraced
smoke timing. There is no stress performance acceptance budget. Repeated context
and trace text duplication remains a concrete storage/memory limitation.

## Limits and next boundary

This closes representation and observable plumbing only. Scripted Dev finals
are not utility/ASR evidence. Collection/context
lineage is conservative, not token/row-level causal attribution. Host source
labels do not classify payload assertions or use evaluator GT. Normalized audit
views remain outside model inputs. No held-out payload parsing, model inference,
network tool side effects, security enforcement or Phase 5 work is authorized by
this acceptance. Existing owner self-review waiver applies; no independent
review is claimed. Raw logs remain local and ignored; selected hash receipts
and reports are the version-controlled evidence.
