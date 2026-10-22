# Safe-email A6 candidate v14 — CPU report

The v14 opt-in runtime was exercised on 2026-09-29 with deterministic
synthetic replay and a local synthetic guard.  The frozen v3 runtime remains
untouched.

Results for the 22-test focused suite:

| control | result |
|---|---|
| public body and exact authorized email | email action executes; final release is `ALLOW` with the public answer |
| private body | email action is denied with `PROVENANCE_SENSITIVE_PAYLOAD` |
| destination outside the exact anchor | denied with `UNAUTHORIZED_DESTINATION` |
| global revoke | no email anchor |
| conditional instruction | no email anchor |
| quoted instruction | no email anchor |
| subject absent from the affirmative send clause | denied with `PROVENANCE_UNKNOWN_CRITICAL_FIELD` |
| protected private subject literal | denied with `PROVENANCE_SENSITIVE_PAYLOAD` |

The public-email case discharges the coarse private-read sensitivity only after
the exact v4 anchor, public body lineage and subject admission checks succeed.
The private case cannot use the same subject exception because the protected
scan catches the private literal.  The candidate metadata records
`authorization_anchors_v4_candidate`,
`host_destination_origin_v4_email_candidate`, and
`value_pre_gate_v2_email_subject_candidate`, with `a6_native_ready=false`.

Validation passed:

* `pytest -q tests/unit/test_value_origin_v4_email_candidate.py tests/unit/test_authorization_anchors_v4.py tests/integration/test_email_origin_candidate_runtime_v14.py` — **22 passed**.
* Ruff on all new source and test files — PASS.
* Mypy on all five new source/test files — PASS.

No Kaggle/API call, benchmark Test input, private ground truth or credential
was loaded.  These results do not promote Phase 5 and do not establish native
GPU cancellation or remote guard quality.
