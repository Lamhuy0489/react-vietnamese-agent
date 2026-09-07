# Mechanical variant authoring v1

Phase 3 only. Input is the immutable canonical selection manifest (source
`dc45ccb`, evidence `d382e07`) and its eight hash-bound batches. No source,
scorer, split assignment, oracle, legitimate task or environmental fact is
rewritten. New files live in `mechanical_variants_v1`, new authoring modules,
tests, manifests and operational notes. Rejected draft v1 is not an input.

## Surface and review contract

Create three variants per selected attack/benign canonical: no diacritics,
one word-boundary underscore, and one U+200B insertion. This yields **210 attack
and 210 benign** records, 120 Dev/90 Test per branch. Code-mix and paraphrase
are explicitly absent; never call three variants a complete five-variant set.

Transform only the attack/benign addition. Keep task, base content, trigger,
resources, authorizations, scope and reference paths unchanged. Protect tools,
source IDs, SQL/JSON identifiers, addresses, numeric literals and exact text
arguments/final lines when they occur in the payload. Protected literals may
retain diacritics: output-string instructions must not silently change the
oracle target. Log protected spans, raw and visible-debug forms as authoring
metadata, never runtime prompt annotations.

The existing mechanical helper produces drafts, not approvals. Deterministic
regeneration, insertion-only reversibility, original literal-span preservation, non-no-op and
pair/identity/group/count checks are required. Review all 140 word-boundary
edits in context under the owner's assistant self-review waiver, recording
hash-bound evidence. No-diacritic and zero-width receive structural QA; this
does not claim independent human language review or arbitrary semantic proof.

## Executable QA and privacy boundary

A separate adapter selects the existing typed, corrected-mechanism, linked,
flow, disclosure or boundary scorer for each canonical. No default fallback
for unknown batch/rule types. Private scorer/rule/utility objects stay out of
public task/overlay/resource views and model messages. Preserve separate
derived-final and final-policy outcomes; do not flatten them into tool effects.

Run fresh offline environments through unchanged Runtime/Tool Broker for each
canonical and mechanical variant, attack and benign branch, safe and negative
reference. Verify complete payload at the exact source trigger, auxiliary
exposures, private-artifact existence and public-only initial context. Require
exact score parity with each canonical's hash-bound historical score. Reference
scripts are predeclared oracle fixtures, not model behavior or ASR/FPR evidence.
Check the shared-quota alternative safe path separately as well.

Every record has unique variant and pair IDs plus canonical, family, group and
split mapping. Traces preserve the canonical task ID required by old scorers;
the unique variant ID and relative trace path identify each invocation in the
new receipt. Fresh Runtime run IDs and environments prevent cross-variant state.

Test-assigned sources are still in authorized pre-seal dataset construction:
reference QA is allowed, but no Test LLM inference or tuning. Record Test-assigned
Replay counts separately from zero held-out model runs. Never retry semantic
failures for an improved score or modify canonical/oracle to make parity pass.

All outputs are fresh/exclusive, with source/input/selection/variant/review hashes.
Mechanical acceptance does not imply full Phase 3 acceptance: 140 code-mix and
140 paraphrase records, their reviews, executable QA, complete release integration
and Test sealing remain necessary.
