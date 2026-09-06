# Expanded canonical candidates v0.2

12 unsplit, review-pending pairs: four adapted from the preserved workbench,
eight newly authored. Three examples per macro category and source type.
Nine annotated template groups; IDs are not proof of independent semantics.
No variants, split, Test freeze or final family acceptance.

`public/` is model-facing task content only. `overlays/` is synthetic environment
input. `private/` and `catalog/` are local authoring/evaluator data and must not
be packaged into inference workers or model prompts. Candidate metadata and
scope are not used as A0 defenses.

Run `scripts/verify_canonical_candidates.py` with fresh ignored raw output and
report paths. Replay scripts verify both safe/negative paths on both pair
branches. They do not measure attack potency or confer human review approval.
Earlier workbench/v1 bytes remain unchanged; no arbitrary duplication to reach
the final 70-family quota is allowed.
