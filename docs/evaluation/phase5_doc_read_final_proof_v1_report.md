# Phase 5 — raw doc_read final proof: paired CPU result

2026-09-24. **The previously missing real-tool final proof is now implemented
and integrated in an opt-in paired CPU adapter.** Five benign controls preserve
exact utility and seven negative controls prevent the declared disclosure.
This is not native LLM quality, Phase 5 acceptance, or general secret protection.

## What changed

[Protocol](phase5_doc_read_final_proof_v1_protocol.md),
[component](../../src/react_agent/security_v1/doc_read_final_proof_v1.py),
[runtime](../../src/react_agent/security_v1/doc_read_final_runtime_v1.py).
The host pins a metadata-only `DocReadApproval` with source ID, `doc_read`,
`/content`, S0 and review reference. The expected approval hash must come from
outside the proof. The host catalog must match before worker startup.

Unlike the earlier one-field component fixture, the proof accepts the original
successful `doc_read` result with exactly `doc_id`, `title`, `content`. It binds
the complete raw document hash, source artifact ID, call ID and `/content`.
It does not create a projected raw root or lower sensitivity/trust. Source
identity, labels, successful snapshot metadata, index admission and ancestry
are checked. Multiple observations of the approved source are conservatively
ambiguous. Title contents never grant final authority.

The exact raw-user request may contain a bounded explicit read list followed
by `Trả content từ <ID>.`; no negated/quoted/extra clauses are accepted. The
whole field must be one ASCII mixed-alphanumeric identifier, length 8–64.
Only an entire final equal to that literal can use the proof override.
Additional private context, another private value or a normalized-only copy
still uses the existing REDACT/DENY gate. Existing v3 PRE/POST, guard, Broker
and loop remain intact; v4 is rebuilt only at FINAL. The new adapter has its
own CPU identity; previous proof/runtime/receipts and stopped pilot are unchanged.

## Predeclared paired matrix

[Selected summary and hashes](../../experiments/manifests/phase5_doc_read_final_cpu_v1.json).
12 conditions, 24 actual paired-process CPU Replay tasks, fresh state/store per
arm. Synthetic approval is persisted before fixture content. Same task, catalog,
environment, mock actions and forced final across arms; expectations remain
in the host-only QA harness, never approval/policy/model inputs.

| Control group | Previous final-only CPU adapter | New raw-doc proof adapter |
|---|---:|---:|
| Exact benign final preserved | 1/5 | 5/5 |
| Declared protected target omitted | 7/7 | 7/7 |
| Tool dispatch/denial parity | 12/12 paired conditions | 12/12 paired conditions |

Benign: S2 collision, S1 collision, trusted public source, trusted private
source, and no collision. Negative: different private final, added context,
zero-width final, poisoned content, title substitution, title instruction
requesting another secret, and duplicate public observation. Each executes
two `doc_read` calls (three for duplicate), with no denied reads in either arm.
These are mechanism controls, not independent attack families or ASR/FPR.
The duplicate case is a conservative no-proof boundary, not proof that every
duplicate public read is malicious; it deliberately sacrifices utility there.

Public titles may contain arbitrary instructions without granting authority;
the target omission tests do not certify a semantic injection detector. The
field grammar does not handle normal prose, room lines, arbitrary paraphrases,
encoded secrets or short identifiers. No claim is made for those forms.

## Audit and preserved aggregation failure

The [runtime auditor](../../src/react_agent/validation/doc_read_final_runtime_audit_v1.py)
requires the expected approval/hash externally, validates receipt scope, then
reuses the frozen raw-artifact replay in memory. No source or receipt file is
rewritten. It checks the recomputed proof, dual index, final artifact and
observable answer against raw traces. This reuses policy code, so it is an
integrity check, not independent policy implementation or authenticated native
source/worker execution. It does not replace a full native Broker/pair audit.

All twelve per-case receipts finished, but the initial runner's final summary
construction passed `protocol` twice to `dict`, raising `TypeError`. No run
should be called COMPLETE from the absent top-level receipt. Fixed only that
aggregation line and added success/failure runner regression tests without
launching workers. The original raw root is preserved unchanged and still has
no runner-produced top-level `receipt.json`.

[Recovery auditor](../../scripts/audit_phase5_doc_read_final_cpu_v1.py) verifies
the externally pinned original declaration, allows exactly the documented
historical runner hash deviation, checks unchanged policy/control/auditor
sources and replays every saved runtime. It recomputes outcomes from recorded
finals and validates all pair checks. Two read-only audits are byte-identical.
No agent/model task was retried to recover this evidence.

Local ignored evidence:

- Raw root: `build/evaluation/phase5_doc_read_final_cpu01/` (937 files).
- Declaration SHA: `2c9bdfb6d2dfef8ede5d01c719da9ac502da50e2b31b7d2f6aa727b15348757e`.
- Selected audit: `build/evaluation/phase5_doc_read_final_cpu_audit01.json`;
  SHA `fe4d3e10933034196d5a2634b1d13af0970199f490a064e6312baa507d662c4e`.
- Repeat audit02 matches byte-for-byte. The selected manifest preserves source
  hashes, the deviation and raw-inventory hash without committing raw logs.

```sh
.venv/bin/python scripts/audit_phase5_doc_read_final_cpu_v1.py \
  --root build/evaluation/phase5_doc_read_final_cpu01 \
  --declaration-sha256 2c9bdfb6d2dfef8ede5d01c719da9ac502da50e2b31b7d2f6aa727b15348757e \
  --output build/evaluation/phase5_doc_read_final_cpu_audit03.json
```

Another machine can run `scripts/run_phase5_doc_read_final_cpu_v1.py --output`
with a fresh path under `build/evaluation`; the fixed runner now writes its
own summary. Fresh IDs/timestamps/raw hashes differ, expected behavior does not.
Do not overwrite existing evidence or treat a regenerated run as the old run.

## Verification and next gate

Component: 40 passing controls, including all S1/S2 × public/private trust
combinations, real wrapper errors, projected/unobserved roots, forged proofs,
wrong pins/paths/call IDs, ancestry and normalized final. Integration: 36 tests
include the paired matrix/repeat audit, six corruptions, admission-before-start
and max-steps/parse/model-error terminals with no released answer. Two runner
aggregation tests pass. These are overlapping with the wider regression run,
not additional benchmark sample sizes. Broad regression: **319 passed, one
strict XFAIL** preserving the stopped prospective pilot's original final leak.

Setup, repository-wide Ruff, mypy (542 source files), knowledge-check and
diff-check pass. Full pytest is
not used because unrelated authoring modules load sealed held-out Test. No
held-out/private benchmark oracle, real external sink or new native model run.
Only synthetic Dev controls were used, as required by the project skills.

Next: native-capable admission/manifest plus full pair/Broker audit for this
candidate, exact-worker package rehearsal and one coherent source freeze.
Then lock fresh prospective metadata/content/run identities and run on Kaggle.
Do not silently reuse the stopped room-pilot source or its old receipt. Current
CPU approvals are self-review fixtures, not owner timing attestations. Native
guard quality, representative utility and graceful OS exit remain open.
No new Kaggle URLs exist to add to the resource directory. No commit/push was
made in this work; Git base c87 is not a source freeze for these files.
