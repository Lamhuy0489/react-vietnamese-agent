# Phase 4 runtime v1 integration contract

Add a separate instrumented runtime; do not edit frozen A0 or primitive v1.
Inputs remain public task, backend, eight-tool registry, host source catalog,
runtime/generation config. Private evaluator/reference objects are not runtime
inputs. The runtime always uses raw messages/arguments/results/final answers.
Optional normalized views are audit-only and never replace model-facing text.

ControlState snapshots hold step/call/turn/retry/terminal counters, not content.
ContextBundle holds immutable message records with system-owned artifact IDs.
Only role/content dictionaries go to the backend. Exact message order, action
serialization, observation wrapper and format correction follow frozen A0.
Malformed outputs are recorded but not appended to context, as in A0; format
correction is a host-owned constant. Model output parents are precisely the
artifact IDs rendered in that turn's bundle (conservative context dependency).

All successful parsed actions have an action artifact plus security-relevant
argument-field artifacts: email to/subject/body, webhook endpoint/payload. Pre
hook sees a frozen control snapshot and action copy; Broker alone executes.
Post hook creates a source snapshot from the observed result and a serialized
result artifact before context insertion. Final hook sees a final artifact.
Pass-through implementations always ALLOW/return original bytes, regardless
of sensitivity/trust/content. DENY/TRANSFORM are reserved interface values;
non-pass-through hooks fail explicitly as unsupported configuration in this
Phase 4 A0 runner, never treated as a research defense.

Host SourceCatalog labels are initialized independently of payload assertions,
tool-returned trust labels and private oracle facts. Exact tool/argument bindings
override conservative defaults. Unknown retrieval sources default S2/UNTRUSTED;
DB defaults S2/TRUSTED (over-approximation, not field-sensitive classification).
Known clean public document/page reads can be bound S0 with host trust labels.
Legacy overlay T0 maps TRUSTED, T1/T2 UNTRUSTED, unchanged for matched branches.

Observed source snapshots are provenance roots with host source IDs and call
metadata, representing external data, not roots for model-generated content.
They retain source-native labels. The rendered ToolResult depends on both its
source snapshot and proposing action; joins may therefore lower its trust or
raise sensitivity. Model and final artifacts conservatively inherit everything
in their actual context. This is dependency tracking, not causal token attribution.

Trace v2 is a new sidecar for context/artifact/control/decision/normalization events; the
unchanged legacy trace is also emitted for exact A0 comparisons. Run IDs/time
are excluded only from parity comparisons. New files include artifacts, edges,
control snapshots, runtime/generation/catalog/profile identity and their hashes.
No hidden reasoning field is requested or collected. Every run has fresh store,
context, Broker and counters. Backend lifecycle remains caller-owned, like A0.

Acceptance here requires tests of exact messages, tool arguments/results,
terminal outcome/final/parse counts, lineage, hooks, no network and fresh outputs.
Use smoke and public Dev inputs; no Test payload/oracle/archive parsing. Broader
clean/attack Dev trajectory sampling, overhead measurements and full Phase 4
closure remain separate until demonstrated. No Kaggle or real-model run needed.

The 21 clean Dev QA cases reuse predeclared Dev-only oracle action/fault scripts;
their private objects are not passed to runtime/catalog/prompts. Final text is
a constant plumbing probe, not a claim of utility completion. The 24 paired
adversarial Dev cases are public trigger/read probes stratified by source type,
also not safe/attack-success evaluation. Smoke retains its 20 frozen Replay
scripts. These distinctions must remain explicit in every report.
