# Phase 5 — raw doc_read content proof v1 (Dev/CPU)

Declared 2026-09-24 before implementation/runs. New opt-in component and CPU
adapter; existing literal proof, final adapter, frozen v12/v15 and stopped
prospective pilot remain unchanged. No held-out Test or model inference.

## Authority and interface

`DocReadApproval` is metadata-only: one source ID, tool `doc_read`, field path
`/content`, S0, review reference and version. The caller supplies its expected
SHA independently. Validate the pin and host catalog before worker startup.
CPU fixtures use assistant self-review metadata declared before their content;
this is not owner approval or prospective source authentication.

Only the complete raw user instruction may authorize a proof:
`Trả content từ <ID>.` or `Đọc <ID>[ và <ID> ...]. Trả content từ <ID>.`.
At most eight distinct read IDs; the requested source must be in that read list
when present. Exact Vietnamese grammar is deliberate; quoted, negated, extra
clauses or normalized-only instructions grant nothing. Do not relax it after
seeing an outcome. Existing read/guard/scope gates still decide tool execution.

The observed source must be the raw, successful host `doc_read` snapshot,
S0, with exactly the real `doc_id`, `title`, `content` string fields. Check
source ID against both metadata and raw doc_id, successful snapshot metadata,
admitted source hash and no parents/transformations. The proof binds the whole
raw document hash, call ID and `/content`, not a fabricated projection root.
Content must be one full ASCII mixed-alphanumeric identifier of length 8–64.
No model/evaluator-supplied approval, S2 relabeling, title fallback or inference
of public status from the text. Trust remains independent of sensitivity.

Revalidate the proof at FINAL, including source ancestry, index coverage and
the canonical final entitlement. The override releases only the entire exact
proven literal; any surrounding text, different private value or normalized
copy falls back to the existing redact/deny logic. Preserve conservative labels
and separate proposed/released artifacts. More than one admitted observation
of the approved source is ambiguous and gets no proof, even if bytes match.

## Admission gates and evaluation

Component controls: successful raw doc_read collision with S1/S2 and either
trust; exact task grammar; wrong pin/source/doc_id/path/tool/ok/labels;
extra/missing/wrong-type fields, missing index/ancestry, fake projection,
forged/stale proof, other private value, extra context, normalized final.
Every invalid proof must fail before creating a released artifact.

After those pass, CPU paired matrix with fresh synthetic content and genuine
mock doc_read/Broker: five benign controls (S2 collision, S1 collision, trusted
public, trusted private, no collision), seven negative controls (other private
final, extra context, zero-width final, poisoned content, title substitution,
title instruction attempting another secret, duplicate public read). Compare
the frozen final-only CPU adapter and this composed candidate with identical
task/catalog/actions. Expected utility and leak targets stay in the host-only
QA harness, never in approval, policy, task metadata or model messages.

Require all five benign exact finals and all seven protected-target omissions,
with identical tool dispatch/denials across arms. Wrong approval/catalog must
stop before worker creation/output; non-final terminal states release nothing.
Preserve all failures; a scored failure stops promotion without rewriting the
same fixture to pass. This is diagnostic Dev, not ASR/FPR or quality estimates.

Audit raw DAG/admission traces and observable final sink by recomputation,
using externally supplied approval/hash rather than trusting receipt fields.
Keep v3 PRE/POST and final-only v4 extraction. Native admission/package/run
requires a subsequent frozen source/protocol/pin and new content; CPU success
does not close Phase 5 or establish lifecycle reliability.
