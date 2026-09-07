# Adversarial release v2: acceptance and sealing

Combine exactly the accepted 420 mechanical and 280 linguistic records; preserve
70 selected canonical pairs, 20 conservative groups and the fixed 40/30 split.
The earlier v1 draft remains rejected. Each branch has 200 Dev/150 Test records.
Five variants per family, one matching benign record per attack. Canonicals are
reference baselines, not extra experimental samples. No family or model selection.

Public runtime fixtures contain only task, environment overlay/resources and
experiment identities. `task` alone is sent to AgentRuntime; overlays/resources
belong exclusively to the tools. Synthetic sensitive values are environment data,
not evaluator labels. Private rules, reference paths and utility oracles remain
in the existing private batch files. Release scoring uses the frozen selected
adapter, including boundary/final-policy and derived disclosure fields, without
fallback. Runtime traces retain canonical task IDs; unique variant/invocation
IDs in the release evidence provide the exact bridge to experimental rows.

Acceptance re-audits 1,692 existing observable reference traces: 280 canonical
standard, 1,400 variant standard and twelve safe alternatives. This is evidence
reuse and re-scoring, not 1,692 new runs. Verify input/source/trace identities,
exact exposure at the primary and declared search trigger, original score parity,
unique run/invocation IDs, complete pair/surface/split coverage, immutable data,
and the independently recorded semantic review under the owner's waiver.
All 732 Test-assigned reference paths were constructed before sealing. No LLM
or held-out model inference occurred. Deterministic compressed trace archive is
a selected frozen artifact; it contains observable events only, no hidden CoT.

Seal binds the four payload files, schema, mapping, archive, canonical selection,
all environment/data/oracle dependencies and exact source. Seal is written only
after acceptance; a committed receipt binds its hash. Later integrity checks may
hash Test bytes but do not parse payloads or execute references. Dev loader never
opens Test files. Test loading requires explicit held-out evaluation scope.
Post-seal changes require a new version and deviation record, not in-place edits.

Before seal, run the full construction suite. After seal, the integration
collection hook excludes historical Phase 3 authoring modules before import
(some load payloads at collection); it does not hide a failing test. Preserve
the recorded pre-seal full-suite result. The post-seal suite adds hash-only
integrity and Dev-only loading tests, without re-running held-out construction
fixtures during development of subsequent phases. No bypass flag is supplied.

Report limitations: scenario families are not 70 independent abstract mechanisms;
output-poisoning has 12 Dev/3 Test families due to grouped allocation. Reviews are
assistant self-review, not independent human review. Exact reference QA proves
bounded solvability/scoring, not unrestricted semantic equivalence or model ASR.
Closing Phase 3 does not authorize Phase 4 or any final model experiment.
