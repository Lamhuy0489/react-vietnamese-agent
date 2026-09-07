# Phase 4 implementation and handoff reference

This concise index covers the plan's proposed design/spec files without duplicating
frozen contracts. Module paths differ from the illustrative plan tree; interfaces
and acceptance semantics are retained. Independent review is owner-waived.

| Plan deliverable | Implementation/specification |
| --- | --- |
| Normalization spec, raw/Unicode/security profiles | [Foundation contract](phase4_foundation_contract.md), [profile catalog](../../configs/normalization/profiles_v1.yaml), `foundation/normalization.py` |
| Artifact schema/store | Foundation contract; immutable `Artifact`, `ArtifactStore` in `foundation/artifacts.py` |
| Sensitivity/trust model and source defaults | Foundation contract plus [closure protocol](phase4_closure_protocol.md); `foundation/source_catalog_v2.py` |
| Provenance spec | Typed parent links, append-only DAG and independent joins in `artifacts.py`; conservative context dependency in runtime contract |
| Integration/ControlState/ContextBundle/hook contracts | [Runtime contract](phase4_runtime_contract.md), `runtime_contracts.py`, `runtime_hooks.py`, `runtime_v1.py` |
| Trace schema v2 | Section below and typed `FoundationEvent`; legacy trace remains separate |
| Phase 4 report | [Acceptance report](phase4_report.md), receipts linked there |

## Trace v2 and observable-only data

`foundation_trace_v2` sidecar has sequence/run_id/task_id/step/event/data_json.
`data_json` is canonical finite JSON; event payloads:

- `artifact`: host artifact ID + content hash (content is in artifact store).
- `context`: immutable ContextBundle, message role/content/artifact IDs; only
  role/content go to model. No metadata, GT or project knowledge in prompts.
- `control`: state counters/status/proposed tool/call ID; no reasoning content.
- `policy_decision`: Pre/Post/Final stage, target artifact, ALLOW with
  A0_PASS_THROUGH/METADATA_ONLY. DENY/TRANSFORM are unsupported in this runner.
- `normalization`: raw/view IDs, profile/version/Unicode version, input/output
  hashes, ordered operation hashes and descriptive features; no classifier.

The store exports immutable artifact JSONL and typed edges separately. System
and user roots, host-observed source snapshots are explicit roots; model/action/
argument/rendered result/final/normalized views retain dependencies. Search roots
represent whole host collections; their catalog lists members. A source-native
S2/TRUSTED DB snapshot can yield an S2/UNTRUSTED rendered observation because
the proposing action depends on model/untrusted user context. This is intentional.

## Run identity and use

Use `FoundationRuntime(...).run_instrumented(public_task, output=fresh_path,
source_catalog=environment_catalog(...))`. Public runtime protocol is unchanged;
every tool still goes through Broker. Runtime v1 output binds runtime config,
generation (temperature 0, max_new_tokens 512, seed 42 by default), Replay
revision, task, catalog hash, schema/profile versions. The launcher receipt adds
Git commit and source/dataset/environment hashes; metadata alone is not a full
experimental identity. Backend is caller-owned and must be fresh per task.

Raw v1 remains authoritative. Audit views are optional and never become source
or model messages. Normalizer decoding is strict UTF-8; invalid surrogates fail,
no replacement decoding/autocorrect/detranslation. YAML profile catalog is a
tested descriptive record, not a second configuration engine.

Keep separate runtime/source versions after a receipt is selected. Source files
and raw datasets in earlier receipts are immutable. Derived results stay ignored;
selected hash receipts, specifications, tests and reports are version controlled.
No graph database required. JSON contents/context and sidecar trace do duplicate
text; see measured storage/peak-memory limits rather than claiming content_ref
deduplication, perfect causality, arbitrary-scale efficiency or security defense.
