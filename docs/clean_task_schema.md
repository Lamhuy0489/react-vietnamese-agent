# Clean Task Schema v1

Phase 2 stores three strict records keyed by `task_id`:

- `CleanPublicTask`: model-safe instruction and grouping metadata.
- `CleanGroundTruth`: private evaluator facts, paths, arguments, evidence, and
  deterministic fault plans.
- `CleanReviewRecord`: automated QA result and explicit owner acceptance.

Only `CleanPublicTask.prompt_payload()` may enter the agent context; it returns
exactly `task_id` and `instruction`. Ground truth and review records are never
passed to the model.

Public records use stable category, template-family, scenario-family, and
instance-group identifiers. Same instance groups cannot cross Dev/Test. Dates
use ISO `YYYY-MM-DD`, money is numeric VND, and entities use stable IDs.

Authorship is represented honestly as `generated_by=codex` plus the original
125/125 `assigned_owner` allocation. It does not claim either owner manually
authored or peer-reviewed generated text.
