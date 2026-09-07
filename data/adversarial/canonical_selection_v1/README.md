# Canonical selection v1

`review.json` records whole-pool self-review under the owner waiver, with
scenario-specific retain/merge rationale for all 72 stored candidates. Earlier
per-pair benign reviews and reference evidence are hash-bound, not replaced.

Seventy retained scenarios are admitted **for variant authoring**. This is not
independent human review, seventy unrelated abstract mechanisms, a sealed Test
benchmark, or whole-Phase-3 acceptance. Existing eight input batches still say
`unassigned/pending`; those historical snapshots remain immutable. The new
selection manifest owns its separate canonical assignment.

Run `scripts/select_adversarial_canonicals.py` with a fresh report path to derive
the exact grouped split; use `--check-existing` to validate an existing manifest
without overwriting it. `--require-acceptance` intentionally exits 2 because
paired variants and a complete release seal are still absent.

The deterministic objective and unavoidable strata imbalance are specified in
[the selection contract](../../../docs/benchmark/canonical_selection_contract.md).
No payloads/private oracle fields are copied into the selection manifest or
knowledge. Existing private evaluator sidecars remain outside runtime inputs.
