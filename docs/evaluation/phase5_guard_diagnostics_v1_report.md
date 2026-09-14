# Phase 5 guard diagnostics — CPU and native composition

2026-09-14. Structural diagnostics, grouped scheduling and native factory
composition have passed CPU QA. No new GPU run; Phase 5 remains unaccepted.

## Evidence already completed

Source `284590d78c50d4da6ed93495ec60b7befaa63301`:
[CPU receipt](../../experiments/manifests/phase5_guard_diagnostics_v1_cpu01.json),
SHA-256 `3cf5a5e1ed2dfcf9cfa1848bbccafba4afa89b02f66b53003d2f4632628c2907`.
Full 2,871 pass/1 optional-tqdm skip in 714.93s; setup/Ruff/mypy362/knowledge pass.
510 source/424 raw hashes rechecked; 169 tracked data hashes unchanged.
40 actual runtime receipts and 25 diagnostic sidecars are synthetic evidence.
The 58 focused tests include parser privacy controls, five-level observer parity,
retirement failure controls and hash-bound Dev schedule selection.

The observer leaves response bytes and parser decisions unchanged. It records
only hashes/counts and bounded error categories/known-field names, excluding
raw response, unknown keys, arbitrary values and validation exception contents.
Sidecar write failure raises a sanitized error; transport failure propagates.
CPU invalid-output controls reproduce the known pair-wide retirement and missing
POST/next-agent generation. The exact subtype of historical native INVALID_OUTPUT
remains unknown because that run did not retain guard response text.

## Native integration CPU QA completed

Source `c7fa18c`: the observer wraps the whole guard progress/policy/attention
factory. This placement preserves exact HF backend checks inside attention,
and ReadyBackend remains outside so readiness ACK does not become a diagnostic.
Agent factory/config matches frozen native_shutdown_v2. Construction remains
lazy and validates paths/snapshot before model allocation.

Independent audit validates the runtime ledger, then joins every returned guard
response to exactly one classification by PID, sequence, request and generation
hash. Missing/extra records, identity drift and category/outcome contradictions
are rejected. Actual real-spawn joins and mutation negatives passed 17 focused
tests (14.64s) before full QA.

Selected [native CPU receipt](../../experiments/manifests/phase5_native_diagnostics_v1_cpu01.json),
source `c7fa18c84147ab37263f5cc52453b073fe0d94c3`, SHA-256
`1ae96fa272782a174d94687ce9c808fc3ab88830023c915a61d2969662b2f994`.
Full **2,888 pass/1 optional native-tqdm skip**, pytest-reported 785.14s;
75 focused pass/64.83s, setup/Ruff/mypy365/knowledge pass. Process wall times
including process startup/exit are 795.48s and 65.51s respectively, as recorded
in the receipt; these are CPU QA timings, not model throughput.

Independent read-only verification found all 515 source/567 raw/169 tracked data
hashes match; the selected receipt is byte-identical to the generated report.
The 51 actual spawned runtime receipts pass ledger/cleanup audits. The receipt's
45 `observed_diagnostics.jsonl` record count includes mutation-negative fixtures;
it is not a count of successful native classifications or a guard-quality score.
The separate invalid-schema join fixture is also covered by the focused suite.
Output `results/phase5_native_diagnostics_v1_cpu01` is closed; do not overwrite or
rerun this identity. No background QA process or new GPU job remains.

## Grouped Dev schedule and remaining implementation

[Schedule](../../experiments/manifests/phase5_grouped_dev_plan_v1.json) selects one
family in each of eight Dev groups by fixed hash ranking, paraphrase and matched
benign branches: 16 cases, 112 A0–A6 runtime tasks. No model outputs were consulted
for selection; only two pinned Dev files were read. Thirty-two remaining families
are listed separately. The schedule contains identifiers/hashes, no task content
or scorer/ground truth, and `dispatch_allowed=false`.

The public fixtures include document, cached-page and database sources, with
linked auxiliary resources for four selected families. Existing scope v3 handles
DOC/CDOC/CACHE while release fixtures use AWB/AUX identities. This is a concrete
host scope/catalog integration issue to cover before claiming benign utility.
Implement bounded namespace/source binding tests against public fixture metadata;
source trust/sensitivity must not be inferred from model text or evaluator truth.
Also retain the known `cho biết` lexical limitation for broader scope work.

Read-only check on 2026-09-14: all 16 selected public trigger actions are
`assessed=false` under `processing_scope_v3.describe_action`. This is a static
scope-parser result, not a measured denial rate or a model result. Four paired
families use database reads; two use documents and two cached pages. The SQL
parser only accepts a bounded `SELECT columns FROM table` shape, so namespace
support alone cannot resolve the database cases. Do not count unassessed actions
as successful security decisions or silently drop these selected families.

The existing `foundation/runtime_qa.py:fixture_catalog` demonstrates the frozen
host mapping: exact tool/canonical arguments, overlay source identity/type,
S0/S1/S2 independently from T0→TRUSTED and T1/T2→UNTRUSTED. The selected pairs
have identical source labels and linked-resource counts across branches. The
public loader `adversarial_release.py` and `authoring/linked_resources.py` do not
import a private oracle. Reuse the public types/builders; do not import a whole
QA suite into the inference worker merely to obtain its catalog helper.

Before dispatch, require bounded document/page/SQL scope positive and negative
controls, exact host metadata binding, and unknown-source conservative defaults.
Source presence is not user authorization: never grant a read just because an
AWB/AUX identifier exists in the fixture. Linked resources do not inherit S0 or
trust from their referring document. Preserve the frozen v3 profile and add a
separate version for any behavior change; keep all 16 preselected cases.

Next: prepare versioned Dev runner/input/catalog manifest, integrate native
diagnostics and read-only artifact joins, then exact offline archive/expanded
preflight before a new Kaggle submission. Freeze run order/checkpoints/retry scope,
and record structured-output coverage, failed tasks, timing and matched controls.
Lifecycle/guard quality/broader scope/final freeze remain open; Phase 5 not accepted.
