# Phase 5 private-record final entitlements v1 report

The host-only `final_entitlement_v1` component exercises explicit raw-user
source/value grants against the run-local typed origin index. It preserves
authorized trusted private values, redacts unauthorized or untrusted values,
and denies normalized-only or incomplete-coverage cases without changing the
proposed final artifact.

The evidence is 12 deterministic synthetic conditions and does not run a model,
Kaggle job or benchmark Dev/Test payload. It is not runtime adoption or a
security/utility/ASR measurement. A future versioned A6 runtime must compose
this component with the existing A6 coarse vetoes and broader origin coverage.

See the [contract](../architecture/phase5_final_entitlements_contract.md),
[selected QA manifest](../../experiments/manifests/phase5_final_entitlements_v1_validation01.json)
and [knowledge note](../../knowledge/final_entitlements_v1.md).
