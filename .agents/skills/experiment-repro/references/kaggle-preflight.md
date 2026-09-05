# Project Kaggle preflight

This applies only to the Vietnamese ReAct repository. Historical failures are
recorded in `../../../../knowledge/kaggle_lessons.md`; do not generalize a
particular Kaggle image or accelerator limitation to every installation.

Before GPU use, run the exact packaged source in local mount simulations:

- Archive mount and Kaggle-expanded archive inside a generated subdirectory.
- No inherited development virtualenv, editable install, or working-directory
  imports: set the frozen project's `src` in every subprocess `PYTHONPATH`.
- Verify manifest and per-file hashes, refuse links/path traversal, and reject
  Test, pool, private GT, review files and credentials in the worker payload.
- Parse and execute all eight tool schemas through the runtime. Include a
  recovery task: a fault adapter must delegate argument validation, not inherit
  an unusable generic BaseModel input contract.
- Run the whole selected public Dev list using a deterministic stub. The
  worker cannot read private oracle answers to construct this stub.
- Confirm per-task durable trace/result checkpoints, input identity checks,
  and resume of missing work without retrying completed semantic failures.

Before upload, commit and push source, retain the validated bundle receipt,
inspect installed CLI help for uncertain flags, verify the chosen account and
quota without printing credentials, and keep Dataset/kernel private. Wait for
Dataset readiness and verify its version before pushing the kernel. Pin model
revision and generation settings. GPU preflight should perform an actual tensor
operation; `cuda.is_available()` alone does not prove image compatibility.

Before replacing a failed attempt, preserve status/logs/checkpoints and classify
the failure. Retry missing/infrastructure-failed work only. A code or dependency
change creates a new run identity and deviation record, never a silent resume.
If the same infrastructure failure occurs twice after a proposed fix, stop GPU
submissions and reproduce it locally or request the missing platform action.
Do not cycle accounts to bypass quota or rerun semantic failures for higher scores.

After completion, download into a fresh run-specific directory. Validate task
coverage, trace order, component hashes and secret exclusion before scoring.
Treat historical model outputs as immutable; use a new evaluation output path.
