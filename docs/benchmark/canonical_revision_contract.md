# Canonical pilot revision v2.2

Revise wording and conservative grouping of the twelve unsplit v2.1 candidates.
This is a dataset-authoring revision, not five linguistic variants, new families,
or a frozen benchmark. Preserve v2.1 and all earlier sources/results byte-for-byte.

## Permitted differences

- Copy public tasks and private scope/reference oracles without byte changes.
- In overlays, change only `attack_text` and `benign_text`. Preserve legitimate
  facts, trigger, source identity/type, category, trust, sensitivity and artifact.
- In catalog records, change only `semantic_group` and `template_group`.
  Original `lineage` still identifies the ancestor's origin, not this revision;
  the revision record separately identifies its parent dataset and task IDs.
- Reuse unchanged `candidate_review_v1` typed-utility sidecars; never send them
  or authoring review records to runtime. Exact old negative scripts must still
  demonstrate the same violations; no model output is used for wording choices.

## Wording and pair QA

Attack instructions keep their original target/action without descriptions that
label themselves fake. Benign additions become task-relevant descriptive content,
not extra instructions to refuse sends or obey a security policy. An assistant
authoring inspection records intended changes for each pair; this is self-review,
not independent human review or proof of general semantic equivalence.

For this revision only, use an advance-declared **0.8–1.25** benign/attack
whitespace-word ratio as a mechanical length gate. It is not a model-token
matching metric or a universal semantic-validity cutoff. Preserve designated
action/destination/source markers; reject explicit self-labelling attack cues
and benign safety-instruction cues. These lexical checks are deliberately narrow
regression guards and do not detect every possible intent or class cue.

Conservatively merge destination substitution across public and sensitive sends,
and extra-document access across document/tool-output sources. With the three
previous shared-template groups retained, twelve candidates form **seven review
units**. Units are anti-leakage grouping decisions, not seven proven-independent
families. No split or variants are authorized by this count.

## Milestone acceptance

Validate allowed field differences, full identity coverage, preserved private/
public bytes, revision review metadata, length/marker guards and group decisions.
Run 48 fresh typed-utility Replays plus network-blocked/reproducibility and
negative mutation tests. Save exact input/source/sidecar hashes and per-case
evidence. Keep canonical approval pending; the 70-family gate remains open.
