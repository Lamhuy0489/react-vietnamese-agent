# Phase 5 — prospective host-source annotation v1

Declared 2026-09-23 after the Dev32 v2 terminal scoring/root-cause audit. The
owner chose a **new public metadata design**, not a post-hoc relabel of the
Dev32 run. This protocol permits only prospective, opt-in experiments with a
fresh source/run identity. The existing `fixture_catalog`, Dev32 inputs/raw,
scorer, model/prompt, and Test seal are unchanged.

An independent host inventory must classify each auxiliary document/page
**before** ingestion and before model output or evaluator scoring is available.
The source owner must verify the classification and record the inventory
version, reviewer/owner, date, and manifest SHA-256 before a model run. The
manifest is public experiment input, never a prompt instruction or evaluator
oracle. The current released Dev fixtures contain no such independent
classification; therefore no existing auxiliary is relabeled by this work.
The code cannot prove when a human made a classification. Its
`pre_ingestion_host_inventory` field is a declared provenance requirement,
not a cryptographic attestation.

The candidate `PairAnnotations` contains a pair ID and exact, sorted,
nonduplicated auxiliary source IDs/types with S0/S1/S2 sensitivity. Trust is
fixed UNTRUSTED; source content cannot promote it. The constructor requires
the exact public Dev attack/benign pair, identical baseline catalogs and
complete auxiliary coverage. Missing/extra source IDs, duplicate entries,
wrong pairs, altered primary bindings and unrecognized fields fail closed.
The resulting catalog is versioned `host_source_catalog_v2_annotations`,
separate from the frozen v1 catalog. Its `identity` is a canonical manifest
hash; a future run must bind that hash and exact source commit in its receipt.

The prospective lock API now wraps those labels in `InventoryPin`: it records
an owner reference, a review-record reference, an explicit UTC declaration
time and a 40-hex source commit. Its SHA-256 covers all fields, including the
labels. `pinned_pair_catalog` requires a **separately predeclared** pin SHA-256
and the run's exact source commit before calling the pair/catalog validator.
The expected SHA must come from a frozen run manifest; computing it from the
presented pin at admission time is circular and provides no lock. A changed
label/review reference, wrong commit or wrong Dev pair is rejected. Tests use
synthetic specimen references, not a real owner endorsement. The commit check
is string equality against an externally supplied run identity; the run
package auditor must separately authenticate that Git commit. Admission also
revalidates Python objects so `model_copy(update=...)` cannot bypass the
schema before the hash comparison.

This is only a structural identity gate. A timestamp or review string can be
typed after the fact; code cannot prove pre-ingestion timing or independent
human judgment. No inventory for the already scored Dev32 has been approved,
and v13 remains synthetic-replay-only. Before prospective model inference,
the owner must actually review the source inventory **before content is
ingested**, preserve that external review record and pin SHA/source commit in
the run manifest, then authenticate the recorded pin at admission. Do not set
`host_inventory_attested=true` merely because this schema validates.

For a rehearsal of content-free declaration order, a separate
[synthetic room draft](phase5_room_synthetic_inventory_v1_report.md) uses new
IDs and CPU Replay only. It has no owner endorsement or approved Dev label,
so it cannot unlock model inference.

Before any runtime use, add a synthetic paired control with public, sensitive,
unknown and poisoned auxiliary sources; separately version a bounded `room`
payload grammar and typed identifier origin path; test PRE, POST and Final
against unsafe exfiltration and benign utility. The existing Dev false block
cannot be resolved by source labels alone: `room` is unsupported and its value
has no typed origin. Only after those independent controls and predeclared
quality/lifecycle acceptance may a **new** Dev run be frozen and submitted.
Never use held-out Test or the scored Dev32 answer to set labels/thresholds.

Current acceptance for this step: schema/constructor/pin and negative unit
tests; 100 related focused tests, setup, Ruff, mypy, knowledge-check and
diff-check pass. No GPU run, source freeze, Kaggle
submission, A6 policy relaxation, ASR/utility improvement or new Phase 5 DoD
group is claimed.
