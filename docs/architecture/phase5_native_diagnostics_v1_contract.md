# Native guard diagnostics integration v1

2026-09-14. Extends the accepted CPU structural observer with native composition
and independent runtime-sidecar audit. Scope remains Phase 5.

The new native constructor uses unchanged model revisions, deadlines, progress,
attention and generation-policy factories. Ready acknowledgement stays outside
the diagnostic wrapper so it is not counted as a model response. The observer
wraps the complete guard progress/policy/attention stack; the exact-type native
loader requirements continue to see the original HF backend. Paths/pins are
validated before loading, and the caller creates native output before start.

Independent auditor first validates the runtime v3 ledger, then requires one
diagnostic per successful returned guard response. Join sequence/PID/request/
generation identity to the guard classification. Reject extra/missing/unknown
fields and contradictory valid/invalid outcomes. Depth/size inspection cannot
determine parser success and must remain unassessed. Response hashes are observer
evidence, not independently recovered native text or authenticated remote source.

Acceptance: lazy topology/pickle/pin/path controls, real-spawn valid and invalid
joins, mutation detection, full setup/Ruff/mypy/pytest, frozen source/data hashes.
Preserve all document/native/diagnostic CPU evidence. No new model run in CPU QA.

Next package still requires a new run identity with this native constructor,
the chosen Dev task/catalog manifests and exact isolated archive/expanded tests.
The existing grouped schedule remains dispatch-disabled; do not use prior GPU
success or CPU tests to assert acceptance of the new native stack.
