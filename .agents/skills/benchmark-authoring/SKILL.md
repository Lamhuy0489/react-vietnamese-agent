---
name: benchmark-authoring
description: Create or review clean tasks, canonical attacks, matched benign controls, or Vietnamese variants for this project's benchmark. Use for benchmark authoring and QA, not model-output tuning.
---

# Benchmark Authoring

Read the applicable contracts before changing data:

- Clean work: `../../../docs/benchmark/clean_contract.md`.
- Attack or benign work: `../../../docs/benchmark/adversarial_contract.md`.
- Any split/freeze work: `../../../docs/benchmark/split_rules.md`.

Author a canonical semantic unit first. Define the legitimate goal, synthetic
environment dependencies, private ground truth, machine-checkable success
conditions, valid/safe tool path, and review metadata. For an attack family,
also define the attack location/objective, authorization, sensitive artifacts,
violation oracle, matched benign control, and utility-preserving safe outcome.

Generate variants only after the canonical and benign pair pass review. Verify
semantic equivalence manually for code-mix/paraphrase and structurally for
no-diacritic/word-boundary/zero-width variants. Run schema, count, pair,
duplicate, solvability, and split-leakage validators.

Never move a canonical family, its variants, or its benign pair across splits.
Do not inspect or modify held-out Test to improve model behavior. Do not retain
real personal data or let mock sinks perform real side effects.
