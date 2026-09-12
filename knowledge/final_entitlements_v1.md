# Private-record final entitlements v1

`final_entitlement_v1` is a host-only component for a future A6 runtime. It
requires an affirmative raw-user final-answer clause naming an exact synthetic
resource/table and value type. It binds that clause by hash to the raw user
artifact and checks complete run-local origin coverage before release.

Trusted origins matching the explicit source and type may remain in the final;
untrusted, wrong-source, wrong-type, normalized-only or uncovered values are
redacted or denied deterministically. Sensitivity/trust labels remain
conservative, and no evaluator grant/model-origin declaration or hidden
reasoning is accepted. The existing public-final policy and runtime v5 are not
modified.

The selected [QA report](../docs/evaluation/phase5_final_entitlements_v1_report.md)
and [manifest](../experiments/manifests/phase5_final_entitlements_v1_validation01.json)
record 12 synthetic conditions, 17 focused tests and clean-release full QA
(2,333 passed / 13 optional-native skips) from commit `7ca96ce`; the stable case
summary is `d5e3e33033289fdb2fe025ce4a05379ca8bcdc34541f7c0826870fe1de357c38`.
This is not runtime adoption, complete semantic provenance, ASR/utility or Phase
5 acceptance. Next: compose with A6 in a new runtime and audit broader origin
coverage without touching Test.
