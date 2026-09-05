# Experiment Protocol

## Run identity

Each run records Git commit, config hash, dataset/environment hash, model name
and immutable revision, generation-config hash, evaluator version, and seed.

## Required behavior

- Freeze all inputs before final inference.
- Start fresh state per task and use deterministic ordering.
- Checkpoint each task; resume only missing/infrastructure-failed work.
- Never cherry-pick successful retries or use best-of evaluation.
- Validate counts, duplicates, missing IDs, hashes, and trace completeness after
  every shard.
- Keep raw inference artifacts immutable and derive metrics/tables/figures by
  script.
- Any post-freeze change requires a deviation log and a defined rerun scope.
