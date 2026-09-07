# Mechanism correction and canonical admission review

2026-09-07. Source `e001c8a`; Phase 3 remains in progress.
[Contract](mechanism_admission_contract.md),
[selected receipt](../../experiments/manifests/phase3_admission_v1_validation01.json),
[review register](../../data/adversarial/admission_review_v1/README.md).

## Corrections demonstrated on observable traces

The old quantity rule missed an additional successful, argument-valid webhook
despite the public task's one-send limit. The old order rule checked a prior
calculation but missed a wrong-valued extra submission before the required
correct submission. Both traces satisfied the old utility and security checks.

`mechanism_batch_v2` changes exactly two rule fields: successful-call quota for
quantity and required business-argument equality for order. Other input bytes
match v1 except README. This is a fixed-scenario oracle, not a general semantic
or data-flow evaluator. No runtime A0 defense, model score or old receipt changes.

Six actual Replay controls/counterexamples run through the Broker: safe,
successful violation and failed violation for each scenario. Old and new rules
score the same traces offline. Both corrected successful violations produce one
proposed and one executed violation. Failed violations produce one proposed and
zero executed violations; they are not labelled safe. Safe controls retain utility.

## Review scope and counts

All 48 candidates have a hash-bound assistant self-review under the owner waiver.
Merge `awb_hexcode` into `awb_encoded` and `awb_rowretry` into `awb_rowdirect`:
encoding/entity or recovery-pretext substitutions do not establish another
canonical scenario in these pairs. Keep their files and regression fixtures.

There are **46 retained representatives**, 15 conservative review groups and
1,128 pair comparisons. Retention means eligibility for later whole-pool
selection, not 46 certified independent families or release approval. At least
24 further retained scenarios are needed for the unchanged target of 70.
Final selection may require further merges. No independent human review is
claimed, and no variants or split were generated.

The current evidence combines **160 reused standard paths** for 40 unchanged
candidates with **32 fresh standard paths** for the revised eight. The six extra
counterexample/control paths make **38 fresh Replay runs**, not 192 fresh runs.
These are deterministic QA fixtures, not LLM experiments or ASR/FPR estimates.
Raw traces remain ignored under `results/phase3_admission_v1_validation01`.

## Verification and next step

- 367 tests pass, including 26 new mutation, no-network and reproducibility tests.
- Setup, Ruff, mypy (126 source files) and clean_v1.1 sealed-read-only validation pass.
- Ten previous receipts: 689 hash entries match, including twelve measured artifacts.
- Selected receipt: 134 source/input/review hash entries and all 38 fresh raw
  trace hashes match. Four credential values checked across 24 changed files:
  zero matches. Knowledge links and handoff structure pass validation.
- The selected verifier returns `valid=true`, `phase3_accepted=false`; exit 2
  with `--require-acceptance` is the intended incomplete-phase gate.
- No LLM/Kaggle or held-out inference. Static integrity checks are not Test tuning.

Next author genuinely distinct canonical/benign pairs, review the complete pool,
then assign grouped 40/30 Dev/Test before generating and reviewing 350 attack
and 350 benign variants. Keep old draft and receipt bytes frozen. Use the new
admission verifier for this snapshot; pool v3 remains historical v1-rule evidence.
