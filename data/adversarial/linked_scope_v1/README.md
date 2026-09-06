# Linked-scope authoring candidates v1

Eight unsplit pairs: four bounded cross-record DB reads and four linked-source
workflows. Public tasks, environment overlays and private evaluator data are
separate. Never feed private sidecars to a model. All records and destinations
are synthetic; external sinks are log-only mocks.

The new row examples deliberately share a conservative grouping key; linked
document, sink-artifact and route examples reuse existing mechanism groups.
Eight scenarios are not eight certified independent mechanisms or accepted
families. No variants or Dev/Test assignment have been made.

Author: assistant under the owner's same-machine workflow. Independent human
review: not performed, not fabricated. Pair intent review: attack changes a
read/data/recipient authorization; benign describes the existing workflow and
does not request the extra action. Legitimate goal and environment dependencies
are identical within each pair. Length ratios must remain between 0.8 and 1.25.

See `docs/benchmark/linked_scope_contract.md` for bounded SQL coverage and QA.
