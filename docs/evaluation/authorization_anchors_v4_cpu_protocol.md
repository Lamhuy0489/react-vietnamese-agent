# Candidate safe-email grammar — CPU protocol

Declared 2026-09-29 after the immutable `remote_gate_controls_v1` and
`encoded_final_api_v1` diagnostics.  This is a local, deterministic Dev
candidate for one observed authorization-grammar defect.  It does not modify
the frozen v3 parser, any prior receipt, the model prompts or the Kaggle
notebooks.

The candidate has exactly two proposed grammar changes:

1. Treat a finite chain such as `Đọc DOC_PRIVATE rồi đọc DOC_PUBLIC` as a
   read-only context clause.  The old v3 grammar only recognized a repeated
   resource list and therefore marked this clause unsupported.
2. Treat `Không công bố hoặc gửi nội dung từ DOC_PRIVATE` as a
   resource-scoped payload prohibition.  It must not revoke an unrelated
   explicit destination grant.  Sensitive payload, provenance and final
   release gates remain independently mandatory.

The CPU matrix contains only synthetic raw-user strings.  It includes the
observed safe-email form, a shorter scoped prohibition, a global revocation,
quoted/reported/conditional instructions, a chained-read send, and a
resource-only prohibition that must not create a destination.  Each row is
scored against both v3 and the opt-in v4 candidate.  The run records clauses,
blocked reason, email/end-point anchors and raw-user hashes.

No benchmark or Test files, ground truth, model, guard, endpoint, credential,
tool execution or network access is loaded.  This is grammar evidence only;
it is not an A6 runtime result, an egress authorization result, guard-quality
evidence or a Phase 5 acceptance gate.  A follow-up runtime integration must
bind v4 through a new versioned runtime and rerun fresh declared Dev controls
before any native/API claim can be made.  It must retain the global-revocation,
quoted, conditional, unknown-destination and sensitive-payload negatives.
