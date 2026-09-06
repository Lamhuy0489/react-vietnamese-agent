# Phase Status

- Current stage: **Phase 2 accepted: clean_v1.1 sealed; Dev pilot audited**
- Setup owner: Lâm Quang Huy
- Last updated: 2026-09-06

## Setup acceptance

- [x] Repository structure and operational docs created.
- [x] Python packaging, lint, typing, and test configuration created.
- [x] Credential paths excluded from Git.
- [x] Four repository-scoped Codex skills created.
- [x] Official Kaggle CLI skill installed and verified.
- [x] GitHub remote created and initial branch pushed.
- [x] Collaborator invitation sent to `minhb5d` with write access.
- [ ] `minhb5d` accepts the GitHub invitation and confirms clone access
  (deferred by the project owner; not a Phase 1 blocker).

## Phase 0 handoff

- [x] Research contract accepted by the project owner.
- [x] Four previously ambiguous design decisions frozen.
- [x] Phase 1 authorized on 2026-09-05.

Phase 1 may proceed on synthetic smoke data while collaborator acceptance is
pending. Held-out benchmark data must not be created or accessed in this phase.

## Phase 1 progress

- [x] Five shared contracts and A0 configuration frozen.
- [x] Backend-neutral runtime, strict parser, broker, logger, and eight tools.
- [x] Synthetic environment and 20 smoke tasks (10 Huy / 10 Minh).
- [x] Local Replay run: 20/20 success, 0 crash, 8/8 tool coverage.
- [x] Local Dummy run: 20/20 terminal states, 0 crash.
- [x] Unit/integration suite: 35 tests passing; package coverage 89%.
- [x] Minh cross-review deferred by explicit owner decision.
- [x] Real-model Kaggle run: 20/20 terminal, 0 crash, artifacts audited.
- [x] Trace audit: 262 schema-valid events and valid tool event ordering.
- [x] Credential-value artifact scan: 0 matches.
- [x] Frozen run manifest and artifact SHA-256 values recorded.

Phase 1 was **accepted on 2026-09-05**. The low A0 semantic score (3/20) is a
recorded limitation, not a completion blocker.

Follow-up audit reconfirmed the eight Phase 1 DoD gates on the smoke scope:
two independent Replay/Dummy CPU runs, normalized trace determinism, and all
eight frozen Kaggle artifact hashes. See `knowledge/integrity_audit_20260905.md`.
This is not a claim that every edge case has an individual regression test.

## Phase 2 progress

- [x] Phase 2 explicitly authorized on 2026-09-05.
- [x] 250 total / 150 Dev / 100 Test and category quotas retained.
- [x] Same-machine workflow recorded; review replaced by automated QA under the
  owner waiver without fabricated reviewer metadata.
- [x] Clean task/ground-truth/automated-QA schemas frozen.
- [x] Frozen synthetic environment built and validated.
- [ ] Pool acceptance: 250 schemas/oracle fixtures pass, but 30 same-instance
  pairs have different group IDs; review booleans are not independent QA evidence.
- [ ] Split acceptance: sealed hashes intact, but 12 semantic instances cross
  Dev/Test. Original v1 files are preserved, not repaired in place.
- [x] Dev-only Kaggle pilot completed without Test/private GT access.
- [ ] Phase 2 acceptance and release tag: blocked by benchmark-integrity defects.

The earlier Phase 2 acceptance claim is **withdrawn** after a static integrity
audit, not after a held-out model run. The Dev pilot remains historical execution
evidence (21 terminal, 0 crashes, 334 events); its 7/21 score is provisional
because argument comparators and typed fact semantics are incomplete.

Owner approved clean_v1.1 replacement and Dev experiments. Replacement progress:

- [x] Independent `data/clean/v1_1` with original v1 bytes preserved.
- [x] 250/250 executable QA, required arguments and all annotated alternative paths.
- [x] Cross-category group assignment: exact 150/100 quotas, no shared group or
  fact/evidence signature across splits; 50 robustness IDs selected before seal.
- [x] Typed numeric/date/set checks and SQL/calculator result equivalence with
  negative-control tests; no fabricated human review claims.
- [x] Public-only 21-task Dummy run and identity-safe checkpoint/resume tests.
- [x] Exact Git-bundle archive/expanded mount simulations, eight runtime tools,
  fault adapter, 21-task Dummy and missing-only resume in both layouts.
- [x] Kaggle v1 COMPLETE on first push: 21 terminal, 0 model errors, 318 valid
  trace events, 5/21 Dev diagnostic success; all checkpoint/input hashes audited.
- [x] Frozen evidence receipt, four credential-secret checks with zero matches.
- [x] Full Phase 2 closure: v1.1 acceptance recorded with the documented
  automated-QA owner waiver; no final Test experiment or Phase 3 start.

v1.1 dataset hash: `692ca92a214b0da87245ca7d11a074a74d416558f377bc448c125bd7d387be38`.
Do not move tasks or rewrite either frozen version. Language-quality review is
waived, not claimed to be proven by the structural tests. Low-level QA is not
equivalent to unrestricted language-quality review. Pilot evidence is in
`experiments/manifests/phase2_clean_v11_kaggle_v1.json`; audit hashes are in
`experiments/manifests/phase2_clean_v11_audit.json`.
The review waiver still applies; no peer review or new account is requested.

Phase 2 is accepted for the frozen synthetic benchmark under the owner waiver.
The pilot is Dev-only diagnostic evidence; held-out Test remains sealed and
must not be accessed without explicit scope. Do not begin Phase 3 yet.
