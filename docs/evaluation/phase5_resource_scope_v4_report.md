# Phase 5 resource scope v4 / runtime v9

2026-09-14. Source `d9f11df`; implementation milestone, not Phase 5 acceptance.
The [contract](../architecture/phase5_resource_scope_v4_contract.md) freezes this
bounded change without replacing historical v3/v8/native results.

## Implemented behavior

Host ResourceBindings validates a finite, canonical resource inventory from exact
SourceCatalog tool/argument/type/identity bindings. AWB/AUX document/page actions
must match that inventory and an affirmative raw-user read anchor. A known but
unrequested auxiliary source is denied before Broker at A4–A6. Case/path/format
changes and extra fields cannot manufacture aliases. A0–A3 do not enable v4.
The exact phrase `cho biết` is recognized inside affirmative read instructions;
negative/conditional/quoted clauses remain rejected. No general language parser
or cross-source authorization inference is claimed.

The public Dev catalog mirrors frozen overlay labels independently of content.
Auxiliary document/page identity and type are known, but their labels remain
S2/UNTRUSTED. An S0 referring source does not make its linked source public.
No evaluator/ground-truth object enters runtime or catalog construction.

The metadata-only grouped schedule is unchanged: eight fixed pairs, 16 cases,
112 prospective A0–A6 tasks, dispatch disabled. Static assessment of the selected
document/page trigger actions changes from 0/8 under v3 to 8/8 under v4. The
other eight SQL triggers remain unassessed; they are neither dropped nor scored
as successful defense. This is not an ASR, FPR or semantic utility measurement.

## Verification

Development focused suite: 75 pass in 25.51s (37 new unit, 20 real-spawn
integration and 18 legacy document-scope regressions). Frozen-source focused QA:
75 pass in 25.18s. Setup/Ruff/mypy371/knowledge pass. Full regression QA:
**2,945 pass/1 optional native-tqdm skip**, pytest-reported 865.40s. Process wall
times including startup/exit are 25.76s focused and 875.85s full, as recorded in
the receipt; these are CPU QA timings, not model performance.

[Selected receipt](../../experiments/manifests/phase5_resource_scope_v4_cpu01.json),
source `d9f11dfb010599c92368ef916a4118e406ba1ed4`, SHA-256
`6735b6205bf6a094cc2fe79cadfd9c522f850870e7d6ada75ebe2a37aa2904d0`.
Independent verification: all 524 source/295 raw/169 tracked-data hashes match;
selected receipt equals generated report byte-for-byte. Historical native
diagnostics receipt still matches all 1,082 source/raw entries. The output
`results/phase5_resource_scope_v4_cpu01` is closed; do not rerun or overwrite it.
No background QA or GPU process remains. This closes bounded CPU acceptance
only, not native lifecycle, guard quality or the full Phase 5 gates.

Integration runs use scripted public trigger proposals and a synthetic SAFE
guard, never oracle-derived success trajectories. Two document/page sources
traverse A0–A6, two further selected source families traverse A6, and four
A3–A6 controls attempt an unrequested auxiliary read. Actual tool-returned public
bytes remain unchanged. Ledger/PID/guard diagnostic joins and cleanup are audited;
network creation is blocked by the host test fixture. These are CPU runtime
plumbing controls, not native model quality or GPU lifecycle evidence.

Focused captured artifacts: 20/20 terminal `completed`, 21 successful tool
results, 37 synthetic guard-response sidecars. V4 scope PRE records contain
11 ALLOW and three DENY; the three denials are the predeclared A4/A5/A6
unrequested-page controls. A3 executes the second read as the lower-level
control. These counts are a test-geometry check, not an inferred population rate.

## Remaining work

1. Bounded SQL row scope: capture projected and predicate columns, exact table
   and row-key/value restrictions without executing SQL outside Broker. Removing
   or widening a WHERE constraint must not be treated as the same scope. Preserve
   table/column pairing, explicit user authorization and conservative unknowns.
2. Host schema/label provenance and broader benign utility: unknown auxiliary
   sensitivity can block legitimate final/sink operations. Do not lower labels
   or infer grants from fixture contents merely to make a benign example pass.
3. Versioned grouped Dev runner/input hashes, checkpoints and exact offline
   package preflight before any new Kaggle submission. Then measure native
   structured-output/guard-path coverage, failed tasks, timing and paired Dev
   quality with all semantic failures retained.

Existing authoring SQL helpers are not runtime dependencies: `data_scope.py`
imports an evaluator and `linked_scope.py` consumes oracle row grants. Do not
reuse them as authorization or pull the private QA dependency tree into workers.
The existing read-only db_query tool supports more SQL than scope v3 can assess;
tool executability alone is not authorization. No SQL or tool behavior changed
in v4. No Test payload, private oracle, native model allocation or GPU run occurred.
