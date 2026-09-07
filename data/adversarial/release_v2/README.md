# Adversarial benchmark v2

70 canonical scenario families, five reviewed variants per branch: 350 attack
and 350 matched benign records. Fixed 40 Dev/30 Test families, twenty conservative
groups; 200 Dev/150 Test records per branch. Canonicals are not extra samples.

Four JSONL files contain public runtime fixtures. Send only `fixture.task` to
AgentRuntime and build tools through `fixture.registry`; environment overlays
and synthetic values are not prompts or evaluator rules. Original canonical
task IDs remain in traces, with unique variant/invocation mapping in the archive.
Private scorers/references remain in the hash-bound source batches.

`qa.json` records pre-seal integration: 1,692 reused/re-scored reference paths,
not fresh model inference. `reference_traces.jsonl.gz` is the selected immutable
observable-event archive. `seal.json`, once present, owns final acceptance;
the pre-seal QA flags intentionally remain false and must never be rewritten.

Use `scripts/assemble_adversarial_release.py --action check` after sealing.
Do not rerun authoring, parse Test failures, or modify data for later development.
The public loader defaults to Dev and requires explicit Test evaluation scope.

Limitations: assistant self-review under the owner waiver, no independent human
review; scenario families are not 70 unrelated abstract mechanisms. Grouped
allocation gives output-poisoning 12 Dev/3 Test families. Exact reference QA is
bounded fixture validation, not a model attack-success rate or general-language
equivalence proof. No real external sink effects or held-out model runs.
