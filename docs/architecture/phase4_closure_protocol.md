# Phase 4 closure protocol v1

Scope fixed before measurement: complete the Phase 4 representation/plumbing
DoD; no Phase 5 enforcement, model-quality claim or held-out content access.
The existing owner self-review waiver applies; no independent review claimed.
Keep frozen A0, foundation runtime v1, primitives and prior receipts unchanged.

## Source metadata adapter

`EnvironmentCatalog` extends the immutable host catalog without changing runtime
v1. It inventories the actual copied environment (IDs, not assertions in content)
and hashes its document/page/DB bytes. Clean CDOC documents default S1/TRUSTED
(internal); clean CPAGE cached pages default S0/UNTRUSTED; database defaults
S2/TRUSTED. These are host initialization rules, not evaluator classifications.
Other/auxiliary IDs default S2/UNTRUSTED. Explicit public overlay source labels
override inventory defaults identically for paired branches. No secret substring
classification, benchmark fact catalog or oracle goes into metadata.

Search snapshots label a whole collection, joining every possible source, not
only returned hits; source ID is a hash-bound collection identity. The catalog
enumerates members; observed result still retains exact hit IDs/snippets.
Database queries join the whole database and public overlay/auxiliary row labels,
regardless of SELECT projection. This deliberately over-approximates dependencies,
does not claim row/token-level attribution, and cannot become an allowlist.
Source-native labels and action-dependent rendered ToolResults remain distinct.

## Dev integration

Reuse/audit the frozen 20 smoke parity results. Fresh 21 preselected clean Dev
reference-action paths use the new metadata adapter. Reference steps/faults stay
in QA, never runtime/catalog/prompts. Select 12 Dev families (three per source),
prioritizing the first linked-resource family when available, then lexical ID;
zero-width/code-mix/paraphrase by family index, both branches: 24 trajectories.
For each: search/read source, read bounded auxiliary resources, query a synthetic
DB row, calculate, simulate email and webhook, final. At most 32 steps on both
runtimes (QA-only bound). Source exposure, ancestors and sink fields are asserted.
Fixed scripts/final markers test plumbing, not legitimate utility or attack ASR.
Auxiliary row metadata defaults conservatively regardless of row content.

All new outputs are fresh under results. Test is hash-only; no Test payload,
Test oracle, authoring selection loader or Test archive parsing. Private clean
Dev references are the only evaluator-side input read, strictly by QA.

## Controlled local overhead measurement

CPU Replay only, all 20 frozen smoke tasks, both A0 legacy and instrumented raw
v1. Each task uses fresh backend/runtime/Broker/store and environment copy.
Registry/environment setup is outside timed sections; runtime creation, context,
execution and logging/export are inside. No model loading/inference or network.
One fresh subprocess per mode/repetition: warm-up pair then seven measured pairs;
alternate legacy/foundation order by repetition. Record each task wall and CPU
time with no allocation tracer. Separate three paired memory repeats use
tracemalloc; report traced current/peak allocations, not those timings. Record
process peak RSS with platform units; it includes interpreter/imports/setup,
is a high-water mark and is not per-task incremental RSS. Log bytes separately.
Total 440 Replay executions (320 timing incl. 40 warm-up + 120 memory).

Report paired per-repeat differences/ratios, median/p95, environment and raw
samples; small local diagnostics, no population significance or GPU inference
speed claim. Prespecified engineering guards on this bounded smoke scope:
p95 added runtime <100 ms/task; maximum foundation traced peak <32 MiB/task.
These absolute budgets do not hide near-zero Replay baseline ratios. If a guard
fails, retain results and investigate; no cherry-picked rerun for a pass.
Also measure one bounded long-document stress pair (64 KiB, eight repeated
reads) separately, including artifact/trace disk duplication and traced peak.
Stress is synthetic non-benchmark QA, not a modification of frozen data.
The long-document stress has no prespecified pass/fail performance threshold;
its measured limitations must be reported, not folded into smoke guard claims.

## Acceptance and reproducibility

Map all 12 phase-plan DoD gates to executable tests/receipts in the closure report.
Record Git source, hash map, schemas/profile versions, runtime/generation config,
Replay revision/seed, dataset/environment hashes, prior evidence hashes, exact
case IDs and raw file hashes. Deterministic QA stable summary must match preflight;
timings are inherently variable and are not required to hash-match.
Do not mark accepted unless quality checks, source/Dev audit, overhead guards,
frozen-seal and evidence-integrity checks all pass. Optional token-level lineage,
content-ref deduplication and security enforcement are not claimed implemented.
