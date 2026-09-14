# SQL row scope v5 / runtime v10 — Phase 5

2026-09-14. Source `3667529`. [Contract](../architecture/phase5_sql_scope_v5_contract.md).
CPU implementation milestone; not native model quality or Phase 5 acceptance.

## Behavior and boundaries

The pure SQL parser captures table, projected columns, predicate key and finite
AWB/AUX row values without executing SQL or importing SQLite/evaluator helpers.
Host metadata binds exact row identity to table/key. Raw-user grants bind each
projected column to that row; the predicate key is tracked but not automatically
granted for projection. Inventory and prior observation never authorize adding
a row/column, dropping WHERE or changing table/key in a row-bound environment.

Scope v5 is enabled only at A4–A6. Separate runtime v10 and pair wrapper preserve
frozen v4/v9, prompt/tool bytes, guard schema/model and transport. Unsupported
SQL fails closed; unfiltered legacy behavior is retained only without a host row
inventory. Exact catalog labels are not broadened to alternative SQL spellings.

Only public pinned Dev files are loaded. All 16 preselected triggers are now
described; static raw-user extraction yields 14 ALLOW and two DENY. The denied
matched CAND_ROWLIST pair lacks explicit projected columns in the supported
language grammar. Do not infer `note` from its expected answer, delete the pair,
change its instruction or count denial as a successful defense. These are scope
coverage counts, not measured model utility, ASR or FPR.

## Development and QA

Initial unit suite: 48 pass. Integration exposed 17 failures caused by parsing
the host table name `awb_notices` as an additional source identity. Corrected
table-role recognition without altering public data; added a direct regression
and ambiguous-source controls. Subsequent 78 tests passed in 40.50s, then
81 tests in 49.01s. Final development focused suite: **120 pass in 40.60s**,
including 53 new unit, 30 actual-spawn integration and 37 resource/Dev regressions.
Setup/Ruff/mypy376/knowledge pass. Full frozen-source QA: **3,028 pass/1 optional
native-tqdm skip**, pytest-reported 847.08s. [Selected receipt](../../experiments/manifests/phase5_sql_scope_v5_cpu01.json),
source `3667529fcc735eb3a02f53f044bc460caca2a6e1`, SHA-256
`fe423d620aaefe424d11ad0936e84b046f6d84c4192dbb4bbd2178713d5258a8`.
Independent verification: 531 source/463 raw/169 tracked-data hashes match;
selected receipt equals generated report byte-for-byte. All 30 runtime receipts
pass cleanup/ledger audits. Output `results/phase5_sql_scope_v5_cpu01` is closed;
do not overwrite or duplicate this run. No background QA or new GPU job remains.

Scripted integration covers public CAND_DATABASE at A0–A6, ENCODED/QUERYLEAK at
A6, four SQL expansion controls at A3–A6, missing-column controls at A4–A6, and
document/page regressions at A6. A synthetic SAFE guard isolates policy plumbing.
Each task has a fresh worker/environment, real Broker execution, immutable
original public tool bytes and ledger/guard sidecar audits. Model quality is not
tested; a terminal `completed` with a scripted constant final is not utility.

Frozen-source focused capture: 120 pass/44.59s; 30 runtime receipts, all terminal
completed, 31 successful tool results, 70 synthetic guard sidecar records. Scope
PRE contains 19 ALLOW and 15 DENY (12 expansion controls plus three missing-column
controls). These are predetermined test counts, not population success rates.

## Next implementation

Build a versioned grouped Dev runner, separate from the frozen single-document
probe. Task key must include variant ID and level, not shared public task_id:
matched attack/benign fixtures share task_id. Preserve all 112 preselected keys.
Pin raw public fixture bytes/Dev release hashes, source commit, environment,
catalog, runtime/profile/config, model revisions, generation and seed. Each task
gets a fresh overlay; no branch payload mix or cross-task worker/memory/cache.

Checkpoint binds task/variant/level, catalog and runtime v10 to raw hashes. Resume
only absent task keys; preserve partial attempts and semantic failures. Independent
audit must check runtime/guard/native evidence and memory recovery; an existing
v3 transport receipt alone does not authenticate runtime v10 or native HF calls.
Native observer must wrap the complete guard stack, with readiness outside it.

Freeze shard membership/order/stop rules before inference. The old seven-level
document probe took roughly three minutes/level including cold loads; 112 Dev
tasks cannot be assumed to fit one 7,200s notebook, especially with longer tasks.
Choose bounded shards before results, retain common run identity and do not merge
incompatible policies. Recheck live quota/access only when submission is ready.
Exact offline archive/expanded preflight and GitHub source precede Kaggle push.
No new notebook/Dataset version or native run exists for this milestone.
