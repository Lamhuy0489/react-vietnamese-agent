# Phase 5 — exact final-literal proof, development protocol v1

Declared 2026-09-24 after the v4 Dev matrix no-go. This is a new opt-in
component candidate, not a modification of frozen v12/v15, the stopped room
pilot, or the Phase 3 benchmark. It addresses one narrow question: when a
mixed-alphanumeric literal also occurs in S1/S2, can the final sink release
**only that exact literal** if the host can prove the literal was already in
the raw user's affirmative echo request or in a separately reviewed S0
structured field requested by the user?

## Trust boundary and frozen interface

The component accepts a final proposal artifact, the current v4 value index,
the canonical v2 final entitlement, and an immutable `FinalLiteralProof`.
The proof is issued from observed raw artifacts, never model output or
evaluator data, and is revalidated at release. Two independent routes:

1. `raw_user_literal`: the *entire* raw user instruction matches
   `Nhắc lại nhãn <IDENTIFIER>.` and the literal appears there verbatim.
2. `reviewed_public_field`: the *entire* raw user instruction matches
   `Trả <field> từ <SOURCE_ID>.`; an external metadata-only approval pins
   that exact document ID and field as S0 before content; the observed source
   is an S0 raw document result with exactly one key/value pair and that key.
   The release caller must supply an expected approval hash independently of
   the proof. An approval object alone is not an attestation of review timing.

The proposal may be released through the proof route **only if the complete
final is byte-identical to the proven literal**, the user/source ancestry and
index coverage pass, and every protected match spans that full literal.
Anything else uses the existing v2 final release (redact or deny); malformed,
forged, stale or wrong-pin proofs fail closed before release. The new route
does not grant surrounding private context, paraphrases, normalized-only
copies or arbitrary secret substrings. It creates a separate released artifact
and observable `FINAL` decision, without editing the proposal.

## CPU development controls and no-go rules

Use fresh synthetic artifacts unrelated to the stopped prospective values.
Positive controls: raw-user echo with S2 collision and reviewed S0 field with
S2 collision (including trusted/untrusted independence). Negative controls:
private-only literal, changed raw user/source content, wrong approval hash,
source not S0, wrong field/source ID, extra final text, partial protected
match, missing ancestry/index coverage, normalized-only view, forged proof,
and invalid user grammar. Preserve v2 behavior for no-proof calls and ensure
v3/v4/v12/v15 are unchanged.

Do not integrate into runtime or submit Kaggle from unit/component evidence.
An independent Dev matrix must measure both leak prevention and benign
collisions before any runtime version; a new prospective protocol, source
commit/pin and fresh content would be required later. No held-out Test,
private benchmark ground truth, model inference or semantic retries are in
scope. Phase 5 acceptance remains unchanged by this component work.
