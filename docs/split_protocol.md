# Clean Dev/Test Split Protocol

Build and validate the complete 250-task pool before assigning a split. Use
seed 2026 and exact per-category 60/40 quotas. Assignment is group-wise by
`instance_group_id`; no manual task movement is allowed without a changelog.

Before sealing, validate schema, oracle solvability, duplicates, source/entity
overlap, consistency, automated QA acceptance, and category/tool coverage. Then write
150 public Dev and 100 public Test records plus aligned private ground-truth
files and hash every task, environment, schema, and manifest component.

After Test is sealed, model runs are Dev-only. Test must not affect prompt,
policy, architecture, model choice, thresholds, or data repair.
