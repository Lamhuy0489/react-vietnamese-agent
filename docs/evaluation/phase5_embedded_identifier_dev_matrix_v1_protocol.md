# Phase 5 — embedded-identifier Dev matrix, declared 2026-09-24

This is a **development diagnostic**, not a new prospective run and not part
of the frozen Phase 3 Dev/Test benchmark. The matrix is hand-authored synthetic
data after the earlier prospective final-leak finding but uses different
identifiers and document wording. It must not be used to rescore or erase that
finding. V3 and opt-in v4 share the same source artifacts and existing
`final_entitlement_release_v2`; only the origin-index implementation changes.

The [case source](../../data/dev/embedded_identifier_v1/cases.json) is
evaluator-only. Its desired outcomes, case group and target literal are never
given to an agent or policy. This CPU diagnostic uses no model and no held-out
Test. Each arm/case starts a fresh synthetic store. The raw user text, source
content, sensitivity and trust are fixed across arms; the proposed final is
forced Replay, not a claim about what a model would generate.

Predeclared groups and interpretation:

- `leak`: six S1/S2 mixed-alphanumeric private literals. The released final
  must omit the target. Require 6/6 for a v4 mechanism pass; report v3 as a
  control, not as a new baseline experiment.
- `benign`: six public/user literals or ordinary words with no sensitive
  matching literal. The proposed final must remain byte-identical. Require
  6/6 for a narrow no-collision utility pass.
- `collision`: three deliberately repeated literals in raw user/public and
  S1/S2 sources. Desired legitimate echo is byte-identical, but origin is
  ambiguous to a lexical final scan. Count suppression separately; **any**
  suppression blocks runtime integration of v4 as-is, even if the six leak
  controls pass. These are utility probes, not proof that release is safe.
- `unsupported`: three out-of-profile/private transformations. Report actual
  behavior without folding them into the 6/6 mechanism denominator. They
  document that v4 cannot claim arbitrary-secret coverage.

Report effect, released text equality/target presence, indexed supplemental
origin count and grouped denominators for both arms. Pin input/script/candidate
hashes in the local receipt. No tuning of the stopped prospective payload,
no semantic retries, no GPU/Kaggle submission and no Phase 5 acceptance change
follow from this matrix.
