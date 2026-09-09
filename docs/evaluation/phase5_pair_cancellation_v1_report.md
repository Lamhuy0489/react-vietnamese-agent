# Combined pair cancellation — CPU milestone

Source `5d326bf68571f35cbdca2aa37051557d95c38c84` implements the separate
[protocol](../architecture/phase5_pair_cancellation_v1_contract.md). Two clean-source
CPU rehearsals passed all three fresh-pair cases. This is not a GPU result or
Phase5 acceptance. Prior small-context GPU measurements remain unchanged.

## Reproduction evidence

[Selected receipt](../../experiments/manifests/phase5_pair_cancellation_v1_validation01.json)
is byte-identical to the first raw receipt. Results directories:
`results/phase5_pair_cancellation_v1_validation01` and `validation02`.
Each contains44raw files plus its receipt; stable summaries match exactly.
Raw bytes differ because genuine PIDs and timings are retained, not normalized.

Each run creates six distinct processes; all12 across both runs were reaped.
In each run:

| Case | Busy worker | Busy cleanup | Idle sibling cleanup |
|---|---|---|---|
| agent_busy | agent | TERMINATE / -15 | GRACEFUL / 0 |
| guard_busy | guard | TERMINATE / -15 | GRACEFUL / 0 |
| guard_ignore_term | guard | KILL / -9 | GRACEFUL / 0 |

All18 recovery samples per run match the synthetic baseline. **These memory
values are simulated**; they do not measure VRAM release or predict native
model shutdown. CPU warm deadlines0.2s are recorded separately from the future
GPU180/120s protocol. Cold deadlines5s; no model loads or model.generate calls.

Both rehearsals checked146prior frozen source entries, the11pair GPU overlay
hashes, clean/adversarial seals and presealed robustness IDs without opening
held-out payloads. Existing pair GPU62raw files are preserved.

To reproduce with committed clean source and a fresh directory:

```sh
.venv/bin/python scripts/probe_phase5_pair_cancellation.py \
  --output results/phase5_pair_cancellation_v1_validation03
```

Tests cover real spawn/timeout/KILL, skipped trials after failure, malformed
memory, baseline drift, missing/wrong busy marker, forbidden commands, source
loading errors, missing handles/reap evidence, and interrupt cleanup. Fake torch
tests exercise both agent devices and guard device1 without loading actual CUDA.

## Remaining gates

Full final-source QA passed:1,389tests/356.32s, including26new tests.
Setup/Ruff/mypy231files/knowledge checks passed. No GPU worker entry point or
exact Kaggle package exists for this cancellation suite yet.
Next: pinned HF factories/entry point, isolated archive+expanded/PAX preflight,
private input/quota verification and one new GPU identity only after passing QA.

The busy diagnostic deliberately does not run native autoregressive generation.
Maximum-context/forced-length stress, production pair runtime integration,
grouped Dev guard/model decision and remaining A4/final scope remain separate.
No owner SIGKILL, detached-child or CUDA-driver-crash guarantee is claimed.
