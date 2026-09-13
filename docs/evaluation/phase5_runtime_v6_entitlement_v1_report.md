# Phase 5 runtime v6 entitlement adapter report

`security_runtime_v6_entitlement_adapter` composes the frozen task-local v5
loop with `final_entitlement_v1` at the A6 final sink. It keeps the existing
Broker, warm-guard and trace lifecycle and changes only the host-bound final
release dependency; `runtime_v5.py` is not modified or duplicated.

The synthetic QA profile covers ten deterministic cases: trusted explicit and
raw-user auto extraction, implicit redaction, wrong-source/untrusted origin,
normalized-only denial, public no-match, parse terminal behavior, A0
pass-through and host hash rejection. It uses only `data/smoke`, starts no real
model or Kaggle job, parses no benchmark Dev/Test payload and does not claim
ASR, utility or semantic provenance completeness.

See the [runtime contract](../architecture/phase5_runtime_v6_entitlement_contract.md),
[selected manifest](../../experiments/manifests/phase5_runtime_v6_entitlement_v1_validation01.json)
and [knowledge note](../../knowledge/runtime_v6_entitlement_v1.md).
