# Clean Benchmark v1 Design

Status: accepted on 2026-09-05.

Clean v1 contains 250 Vietnamese tasks grounded only in `clean_env_v1`. Public
task records and evaluator-only ground truth are physically separate. The
model-facing adapter exposes only `task_id` and `instruction`; authoring,
category, split, oracle, tool path, answer facts, and fault plans are excluded
from prompts.

## Composition

| Category | Pool | Dev | Test |
|---|---:|---:|---:|
| Single source | 40 | 24 | 16 |
| Parameter extraction | 40 | 24 | 16 |
| Multi-step | 50 | 30 | 20 |
| Database + document | 40 | 24 | 16 |
| Ambiguous | 25 | 15 | 10 |
| Error recovery | 30 | 18 | 12 |
| No tool | 25 | 15 | 10 |
| **Total** | **250** | **150** | **100** |

The environment has 50 synthetic documents, 25 offline cached pages, and eight
SQLite tables. All calls use the Phase 1 Tool Broker. Email and webhook tools
are log-only mocks; cached-page tools never use HTTP.

## Authoring and QA flow

1. Generate and validate the complete unsplit pool.
2. Validate 250 schemas, public/private joins, owner allocation, exact and
   accent-insensitive duplicates, fuzzy candidates, tool coverage, and every
   deterministic oracle.
3. Execute oracle calls through Tool Broker, including private deterministic
   fault injection for recovery tasks.
4. Stratify by category and `instance_group_id` using seed 2026.
5. Seal 100 Test tasks and their private ground truth with component hashes.
6. Run model pilots only on selected public Dev tasks.

The approved same-machine workflow replaces independent peer review with all
ten automated checks under the explicit project-owner review waiver. No
reviewer name or task-by-task owner inspection is fabricated. This deviation is recorded in the
decision log and data card.

## Frozen identity

- Benchmark: `clean_v1.0`
- Environment: `clean_env_v1`
- Schema: `clean_task_v1` / `clean_ground_truth_v1`
- Split: stratified group, seed 2026
- Dataset hash: `2a98633481ac82ae77dbbbe96877d67a3353894ce869e54947e0cf5335371c62`
- Frozen source commit: `5354c0e00faf7ea77ab7063b4c583e9783c0a1ec`

The complete component list and hashes are in
`data/clean/v1/manifests/benchmark_manifest.json`.

## Dev pilot

The accepted Kaggle v2 pilot ran Qwen2.5-3B-Instruct on 21 public Dev tasks,
three per category. It produced 21/21 terminal runs, zero model crashes, 334
schema-valid trace events, and 7/21 strict task successes. The worker bundle
contained no Test or private ground truth. Low baseline performance was retained
without changing frozen Test, prompt, policy, architecture, or thresholds.
