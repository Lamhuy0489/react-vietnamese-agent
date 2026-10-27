# Structured Plan API diagnostic v1

Declared 2026-09-28 before inference. One synthetic component task, not a
benchmark, quality estimate, cumulative A0–A6 run or Phase 5 acceptance.

- Inputs: existing `run_phase5_field_reference_v1.py` prose fixture, three
  synthetic documents, host catalog and grant. No benchmark/Test/private oracle.
- Read all three through the Tool Broker; one fresh Session, grant and guard.
- Agent: Qwen3-8B, inline Plan schema, greedy, seed42, max1024 tokens.
- Guard: Llama3.2-3B-Instruct, fixed guard schema, greedy, seed42, max128 tokens.
- At most one agent and one guard generation. The guard sees the typed proposal
  as candidate content. SAFE permits the diagnostic upstream veto only; the host
  still validates ownership, hashes, selectors and sensitivity before release.
- Same worker source/model mounts as release01; fresh release02a sessions/v2.
  Probe exact identities before inference and save them with working-tree hashes.
- Fresh output only; declaration and started record before generation. Any
  incomplete started record is uncertain and cannot be automatically retried.
  Rejection, timeout, invalid Plan and denial are retained as terminal outcomes.
- Inspect saved Plan validity, actual Broker events, guard verdict, host decision,
  attempts and hashes. A terminal checkpoint does not mean semantic success.
- Model has no host sensitivity labels in its input; this diagnostic cannot
  establish correct public/private field selection. The host controls release.
- No remote shutdown, full runtime integration, lifecycle acceptance, policy
  tuning or promotion of this prototype into the formal A6 baseline.

Command from repository root after both endpoints authenticate:

```bash
.venv/bin/python scripts/run_structured_plan_diagnostic_v1.py \
  --directory build/kaggle/structured_pair_release02a \
  --output build/evaluation/structured_plan_api_v1/diagnostic01
```

Frozen inputs and earlier pilot errors remain unchanged. CPU tests execute with
`build/structured_api_venv/bin/python -m pytest` because exact worker schema
admission needs optional `jsonschema`, absent from the minimal `.venv`.
