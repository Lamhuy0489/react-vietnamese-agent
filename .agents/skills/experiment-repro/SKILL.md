---
name: experiment-repro
description: Prepare, run, resume, audit, or package experiments for the Vietnamese ReAct agent with frozen inputs, stable run identities, safe retries, and held-out Test protection.
---

# Experiment Repro

Read `../../../docs/evaluation/experiment_protocol.md` and
`../../../docs/project/invariants.md` before any final or held-out run.

Before inference, verify and record the Git commit, config hash, dataset and
environment hash, model immutable revision, generation hash, evaluator version,
and seed. Confirm the expected task IDs/count, one fresh state per task, and a
write location outside frozen inputs.

During a run, checkpoint after each task and keep complete observable traces.
Resume only missing tasks or documented infrastructure failures. Never retry a
semantic failure for a better answer, cherry-pick attempts, or combine outputs
from incompatible manifests.

Afterward, audit hashes, task coverage, duplicate IDs, missing outputs, shard
compatibility, and immutable raw artifacts. Re-score saved traces without new
inference where possible. A post-freeze change requires a deviation record and
an explicit rerun scope.

Never use held-out Test failures to modify prompts, policies, thresholds,
architecture, model choice, or dataset content.

Follow the project [commit cadence](../react-vn-capstone/SKILL.md#commit-cadence-for-this-project):
batch finished, verified work; a required experiment source freeze is an explicit
exception, not a reason to commit every preparation or receipt update.

## Kaggle runs in this repository

Before packaging, uploading, or resuming a Kaggle run, read
`references/kaggle-preflight.md`. Use the installed `kaggle-cli` skill for CLI
syntax, and this project reference for bundle/runtime acceptance. Local source
tests alone are not evidence that the uploaded bundle imports or executes.
