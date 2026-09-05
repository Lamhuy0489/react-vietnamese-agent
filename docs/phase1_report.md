# Phase 1 Progress Report

Last updated: 2026-09-05.

## Completed locally

- Frozen strict model/tool/task/trace schemas.
- Backend-neutral runtime with bounded format retry and max-step termination.
- Dummy, Replay, and thin Hugging Face adapter backends.
- Tool Registry and mandatory Tool Broker.
- All eight deterministic mock tools.
- Synthetic 10-document, 10-page, and SQLite fixture environment.
- Exactly 20 smoke tasks with 10/10 designated ownership.
- Observable JSONL traces and run metadata.
- Replay smoke run: 20 terminal, 20 successful, zero crash, eight tools covered.
- Automated validation, lint, strict typing, tests, and CI configuration.

## Accepted Kaggle evidence

- Qwen2.5-3B-Instruct frozen at
  `qwen-lm/qwen2.5/transformers/3b-instruct/1`.
- Private kernel v4 completed on NVIDIA T4 with internet disabled.
- 20/20 tasks reached terminal status; 0 crashes; 262 schema-valid trace events.
- 16 completed answers, 2 max-step terminations, 2 parse failures.
- 3/20 tasks met exact expected behavior; schema validity was 78.87%.
- Real model exercised 6/8 tools; Replay exercised all 8/8.
- Artifact scan against all local credential secret values found 0 matches.
- Frozen identities and SHA-256 hashes are recorded in
  `experiments/manifests/phase1_kaggle_v4.json`.

## Known limitations

- The 3B A0 model often selects the wrong retrieval tool or forms ineffective
  SQL/arguments.
- Sink tasks caused format failures, so the real-model run did not invoke the
  two mock sink tools; deterministic Replay verifies both paths.
- Semantic smoke success is 3/20. Phase 1 targets execution integrity, not high
  accuracy, so this result was retained without quality-based retries.
- Kaggle attempts v1-v3 failed before inference due to mount/import packaging;
  all are recorded as infrastructure failures in the decision log.

## Acceptance decision

The project owner deferred Minh's review. With that explicit waiver, all eight
technical Definition-of-Done checks in `plan/phase1.md` pass. Phase 1 is
accepted on 2026-09-05; Phase 2 remains not started.

No held-out Test data has been created or accessed.
