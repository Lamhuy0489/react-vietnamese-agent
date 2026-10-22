# Safe-email A6 candidate v14 — CPU protocol

Declared 2026-09-29 as a new, bounded candidate after the immutable remote
gate and encoded-final diagnostics.  The frozen v3 authorization parser,
value-origin index, runtime, Kaggle notebooks, API session journals and prior
receipts are unchanged.

This candidate binds three versioned components only for local synthetic Dev
controls:

* `authorization_anchors_v4_candidate` recognizes a repeated read chain and a
  resource-scoped private-payload prohibition while retaining fail-closed
  global revoke, quotation, reported and conditional handling.
* `host_destination_origin_v4_email_candidate` pairs the v4 raw-user parser
  with the host-root origin profile.  The v3 lexical extractor already records
  email-shaped text; the candidate must not create authority from model or
  tool artifacts and currently produces the same records as v3 for this
  grammar.
* `value_pre_gate_v2_email_subject_candidate` admits only a short subject that
  occurs in the affirmative v4 send clause, has an exact authorized
  destination, and has no protected match.  Body, destination, private
  payload, unknown fields and every non-authorized destination remain governed
  by the frozen fail-closed checks.

The matrix uses only synthetic documents and deterministic replay actions.  It
covers: safe public email, private-body email, wrong destination, global
revocation, conditional instruction, quoted instruction, a subject absent from
the affirmative clause, and a subject equal to a protected private literal.
The focused suite has 22 passing tests, zero model requests and zero network
requests.  It uses no benchmark Test data, private oracle, Kaggle endpoint or
credential.

This is component/runtime evidence only.  `a6_native_ready=false`, no API
inference was run, and Phase 5 is not accepted.  A future API Dev run must
declare a fresh manifest, pin both current notebook identities, retain all
negative controls, and rerun the evaluator without changing the frozen Test
split.
