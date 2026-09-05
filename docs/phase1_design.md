# Phase 1 Design — A0 Vertical Slice

Status: local CPU vertical slice implemented; frozen Kaggle run package ready.

## Objective

Prove the observable execution path:

```text
Task → Backend → Strict parser → Tool Broker → Mock tool → Observation
     → Backend → Final answer → JSONL trace
```

A0 provides structural validation, read-only capability boundaries, timeouts,
bounded retries/steps, deterministic tools, and logging. It deliberately has no
injection detection, content blocklist, sensitivity/trust tracking, provenance,
or final-answer security filter.

## Frozen interfaces

- `AgentTurn`: exactly one strict `action` or `final_answer` object.
- `ToolCall`: runtime-generated six-digit call ID, name, arguments.
- `ToolResult`: common success/error envelope.
- `SmokeTask`: public instruction plus smoke-only expected behavior.
- `TraceEvent`: observable event name, run/task/step IDs, optional call ID, data.

The runtime depends on the `LLMBackend` protocol, not Transformers. Dummy and
Replay backends run on CPU; `HFBackend` adapts a preloaded Kaggle generator.

## Frozen Kaggle smoke condition

- Model: `qwen-lm/qwen2.5/transformers/3b-instruct/1`.
- Runtime: private Kaggle script, NVIDIA T4, internet disabled.
- Source transport: private Kaggle Dataset made only from `git archive HEAD`.
- Execution order: one-task preflight, then a fresh full 20-task run.
- Retry rule: rerun only for an infrastructure failure; never select outputs by
  answer quality.
- Secrets: credentials remain local and are never copied into the bundle.

Create the upload folders from a clean committed worktree with:

```bash
make kaggle-bundle
```

## Limits

- Maximum tool/model steps: 8.
- Maximum format retries per step: 2.
- Tool timeout: 5 seconds.
- Search top-k: 1–10.
- Database: one read-only `SELECT`, at most 100 rows.

## Current local evidence

- 20/20 replay runs completed.
- 20/20 smoke success under frozen replay trajectories.
- Eight of eight tools executed.
- Zero crashes.
- One intentionally malformed output recovered.
- 32 automated tests pass; measured package coverage is 89%.

These are infrastructure checks, not thesis results.

Validate any saved run with:

```bash
python scripts/validate_phase1_run.py results/phase1/<run_id>
```
