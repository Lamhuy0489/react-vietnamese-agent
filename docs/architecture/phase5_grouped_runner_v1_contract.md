# Grouped Dev CPU runner v1

Versioned execution/checkpoint infrastructure for the preselected eight paired
Dev groups. Preserve frozen scope v5/runtime v10, data, models and prior results.
CPU-only plumbing profile; no native dispatch, new GPU run or quality scoring.

Use all 112 keys `variant_id__level`, never shared public task_id. Eight shards
contain one preselected matched pair each, 14 tasks in level-major attack/benign
order. Shard/selection/order cannot depend on outputs. Each task builds a fresh
public environment and task-owned agent/guard; A0/A1 have no guard. Synthetic
agent emits the public trigger and a constant final, SAFE guard observes both
branches. This is not semantic utility, ASR/FPR or a native preregistration.

Identity binds source commit, both pinned Dev file hashes, entire clean environment
inventory, public fixture hashes, task instruction hashes, exact host catalogs,
group/pair/variant IDs, runtime v10, A0–A6 configs, generation and execution config,
synthetic backend identity and scripted-response profile. Only raw instruction
enters runtime; selection/branch/oracle metadata never enters model prompts.

Checkpoint binds identity hash, exact task key, terminal, runtime input/metadata,
source catalog, guard diagnostics and raw files including fresh overlay inventory.
Independent audit joins existing v3 runtime ledger and structural sidecars, then
verifies task ID/hash, level, runtime/profile, catalogs, config and results.
CPU receipts do not claim GPU recovery or native authentication.

Before any new work on resume, audit every saved checkpoint and reject unknown
keys, identity mismatch, gaps, symlinks, extra files and partial task directories.
Only an exact completed prefix can continue. A controlled task-count stop writes
no partial task; no semantic failures are retried. Terminal failures are retained.
Output must be fresh and outside input/frozen data roots; no overlapping writes.
Audit and completed resume are read-only. Never overwrite a final receipt.

Acceptance: all 112 keys on real-spawn scripted CPU runtime; paired branch
isolation, shard geometry, interrupted/resumed exact-prefix behavior, runtime and
checkpoint tampering negatives, failure retention, unchanged source/data hashes,
full setup/Ruff/mypy/pytest/knowledge QA. Native factory/VRAM/sidecar joins, exact
archive/expanded Kaggle package and later Dev quality remain separate gates.
