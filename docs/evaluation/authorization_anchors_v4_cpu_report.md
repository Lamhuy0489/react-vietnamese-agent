# Candidate safe-email grammar — CPU report

The opt-in `raw_user_clause_anchors_v4_candidate` parser was checked against
eight predeclared synthetic controls on 2026-09-29.  All controls passed the
expected candidate/v3 comparison.  The original v3 implementation and all
frozen API receipts remain unchanged.

The observed defect is reproduced: v3 marks the combined instruction
`Đọc DOC_GATEPRIVATE rồi đọc DOC_GATEPUBLIC ... Không công bố hoặc gửi nội
dung từ DOC_GATEPRIVATE` as a global `revocation` and extracts no email.  v4
recognizes the repeated-read clause and classifies the final prohibition as
`payload_prohibition`, retaining the explicit `audit@example.invalid` anchor.

The candidate still blocks unscoped `Không gửi`, explicit `Hủy yêu cầu`,
conditional, quoted and reported instructions.  A resource prohibition without
an affirmative send clause produces no destination anchor.  Exact destination
matching remains in force; this parser does not authorize a payload, a final
answer, a sensitive source or a transformed value.

Validation: the v3/v4 focused parser suite plus the opt-in runtime binding
passed **70 tests** (including all existing v3 tests), and Ruff passed for the
new module and tests.  The A2 integration case reaches the declared email
action, while the A0 parity case matches the frozen v12 runtime.  The matrix
is CPU-only and did not call either Kaggle notebook.  It therefore does not
show that a full A6 runtime will allow the safe email, nor that a private email
or payload is safe to send.  Those claims require a separately versioned
runtime/API Dev run with the same negative controls; the candidate explicitly
marks A6 native readiness false.
