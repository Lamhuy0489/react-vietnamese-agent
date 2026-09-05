# Phase 1 Design — A0 Vertical Slice

Status: local CPU vertical slice implemented; real-model Kaggle smoke pending.

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
