# A6 value-origin primitives v1 — bounded component milestone

Scope: plan XXXVIII–XLII and LI–LV. New modules/tests only; A0–A5 and all selected
source remain immutable. Synthetic component QA, no model/Dev/Test experiment.
This milestone does not enable A6 in the ReAct runtime or accept Phase 5.

## Origin evidence, not causal attribution

The host adds observed raw USER roots or tool-source snapshot roots from its
run-local ArtifactStore, supplying the observation step. Derived model output,
finals, argument artifacts, normalization views, roots with transformation metadata
and generated copies cannot be
registered as new origins. Future/cross-run/invalid origins are errors. Duplicate
admission is idempotent. Source labels come from the host, never from text/GT.
Sensitivity and trust remain independent; all matching origins are retained.
The same value in public and protected sources keeps the maximum sensitivity.
User destination authorization will require the existing raw-user anchor policy,
not presence of an email in this index alone.

Exposure lineage remains unchanged. Typed exact matching gives observable value
evidence only, not proof that the LLM used a source. No declassification of raw
artifacts or automatic promotion of trust. No model-produced origin annotations.

## Frozen extraction/matching profile

- Structured field aliases: email, endpoint/url, student_id, course_code, phone,
  gpa, amount/money, date, internal_record_id/record_id. Match fields casefolded.
  DATABASE `columns`/`rows` snapshots from the frozen db_query tool are mapped
  positionally to these types, rejecting duplicate columns and malformed rows.
  This trusts declared column names only for extraction type, not for security
  labels. Unknown/renamed SQL aliases are unassessed; no SQL semantic provenance.
- Free text: whole nonblank scalar strings of 12–32768 characters, except typed
  fields and whole lexical tokens (which retain their token boundaries); lexical email,
  URL, SV plus 6–12 digits, uppercase course codes with 2–6 letters/3–4 digits,
  and ISO dates. PHONE/IDENTIFIER/numeric GPA/MONEY require structured field types.
- GPA range 0–4; MONEY finite decimal. Numeric equivalence uses Decimal, no
  float tolerance; booleans are not numbers. Unlabelled common numbers (1, 2,
  2026) are not indexed. Numeric detection scans bounded plain decimal tokens;
  integral GPA/MONEY matches require an adjacent typed cue (gpa/amount/money or
  Vietnamese equivalents). No exponent notation, locale commas or derivation.
- Exact query is type-specific and case-sensitive for strings. No substring,
  domain-only, Unicode normalization or URL decode can authorize a destination.
- Protected scan searches all protected values in raw text with lexical boundaries
  for tokens and exact spans for long free text. Unicode security_v1-normalized
  matching is detection-only: normalized-only evidence triggers whole-output DENY
  because no verified raw offset mapping exists. It cannot authorize or downgrade.
- Limits: 128 KiB source/output bytes, 32 JSON levels, 10000 records, 4096 sources,
  8 MiB serialized record bytes, 4096 matches,
  8388608 protected-record × candidate-character scan work units. No silent
  truncation: failed admission retires index completeness for the task, atomically
  preserving prior evidence. A failed scan is fail-closed at the release gate.
  A protected value that normalizes to empty/blank text makes the scan unavailable;
  it never becomes a zero-length match or an uncaught validation error.

## Final release component

Input is a host-stored FINAL_RESPONSE artifact from this run, after all admitted
sources. Proposed artifact is immutable. Default clearance is S0, so both S1/S2
matches are protected in this bounded component. This does not decide legitimate
user access to private records; task-specific final authorization and unknown
critical relations still need a separate runtime policy, never evaluator grants.

Exact raw spans are merged and replaced deterministically with `[REDACTED]`.
No LLM rewrite/retry. Normalized-only hits, index/scan errors, an unsafe replacement
or a residual protected hit cause DENY with empty released content. If no protected
match is found, ALLOW means **no match under this profile**, not proof of safety.

A new released FINAL_RESPONSE artifact links the proposal and matched raw roots;
all inherited sensitivity/trust labels remain conservative even after redaction.
The separate decision authorizes release; it does not rewrite artifact labels.
Record proposed/released IDs and hashes, index identity, reasons, origin matches
and spans; do not collect reasoning. Future runtime must return released content,
not the proposed answer, and separately account for proposed vs released finals.

## Explicit limits and next integration

No paraphrase/encoded/translated leakage guarantee; no complete extraction from
unstructured prose or short names; unlabelled integral numbers are intentionally
unassessed. No full action payload decomposition, Pre/Post runtime policy, safe
context views, general authorization or A6 session-veto arbitration in this patch.
Keep A6 runtime rejection until those are integrated and audited. Do not report
these synthetic component results as ASR, utility, LLM quality or full FinalGate.

Acceptance: typed ambiguity/boundaries/numeric/common-value controls, Unicode
detection-only behavior, raw preservation, no origin laundering, fresh/monotone
state, atomic limits, deterministic redaction/deny and serialized artifact audit;
all repository quality gates and prior source/sealed-input hash verification.
