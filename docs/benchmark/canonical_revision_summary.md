# Canonical pilot v2.2 — revision evidence

Date: 2026-09-06. Twelve revised candidates, not twelve additional families.
Parent v2.1 is preserved. No variants, Test allocation, model inference or A0
changes. This milestone implements the assistant review findings recorded in
[candidate review notes](candidate_review_notes.md).

## What changed

- All twelve attack additions retain their target actions/destinations without
  labelling themselves fake. All twelve benign additions describe task-relevant
  information rather than adding instructions to refuse or avoid extra actions.
- Public task and private oracle files are byte-identical to the parent.
  Overlay changes are restricted to the two text fields; catalog changes are
  restricted to semantic/template groups. Base facts and environment metadata
  are unchanged. Typed-utility sidecars and reference scripts are reused.
- Explicit assistant author self-review records document each wording/group
  decision. They do not name Huy/Minh as reviewers or fabricate human approval.
- Benign/attack whitespace-word ratios are 1.0278–1.1333, passing the declared
  0.8–1.25 revision gate. The parent range was 1.0270–1.7391. This is a length
  diagnostic, not a scientific token-matched language-quality metric.

## Conservative review units

| Unit | Candidate IDs |
|---|---|
| Authority side effect | `awb_document`, `awb_emergency` |
| Destination substitution | `awb_cache`, `awb_redirect`, `awb_webhook` |
| Private field to final | `awb_database` |
| Mandatory validation send | `awb_output`, `awb_telemetry` |
| Extra document access | `awb_scope`, `awb_followup` |
| Embedded role command | `awb_quoted` |
| Extra data at authorized recipient | `awb_mail` |

Seven units result from two additional conservative merges; prior linked groups
are never split apart. Different sensitivity/source/sink conditions remain in
their original per-candidate oracles. Grouping them does not collapse those
authorization distinctions or certify seven independent benchmark families.

## Verification

- 48 fresh Replay runs (24 safe/24 negative) have exactly the same per-case
  typed utility/security scores as the parent review receipt. Payloads remain
  reachable and runtime private-data separation checks still pass.
- 244 total tests pass, including 24 new revision tests. These check forbidden
  field edits, parent byte preservation, target edits even with weakened marker
  annotations, direct private-value insertion, group splitting, fake approval,
  length/cue regressions, no network and normalized execution reproducibility.
- Setup, Ruff, mypy (112 source files) and clean_v1.1 sealed validation pass.
- [Selected receipt](../../experiments/manifests/phase3_canonical_revision_v22_validation01.json)
  records exact parent/revision/sidecar/source hashes and raw trace hashes.
  Raw preflight and selected run outputs remain separate under ignored results.

## Remaining limitations and next step

Lexical guards and word-length matching do not certify semantic equivalence or
remove every class cue. Public tasks retain their explicit scope restrictions.
Typed utility remains presence-plus-source-evidence, not general entailment;
scope/leakage limits remain unchanged. Canonical approval and variants are pending.

Next: author additional genuinely different canonical mechanisms in a new batch,
using these reviewed pilot groups to avoid renamed duplicates. Prioritize missing
retrieval/search and multi-step source coverage; extend source/utility/oracle
interfaces only as required by those cases, with negative QA before counting them.
Do not regenerate these twelve merely to increase counts, and do not split until
the canonical pool satisfies the research contract.
