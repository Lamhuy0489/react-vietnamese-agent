# Runtime v6 final-entitlement adapter

`security_runtime_v6_entitlement_adapter` is a versioned host-only A6
composition over the frozen task-local v5 loop. It injects the final-bound
dependency through a per-call function map, so the established Broker,
warm-guard, A0–A5 policy and observable trace lifecycle remain unchanged.
`runtime_v5.py` is not edited and no second ReAct loop is maintained.

The adapter requires an optional host `FinalEntitlement` to be hash-bound to
the raw task instruction before execution. If omitted, the raw user clause is
extracted at the final sink; extraction failure becomes an empty grant. The
same run-local typed origin index, exact ancestry and complete source coverage
rules remain mandatory. Trusted exact source/table/value-type matches can be
released; untrusted, mismatched, normalized-only or uncovered values are
redacted or denied.

The [QA report](../docs/evaluation/phase5_runtime_v6_entitlement_v1_report.md)
records the preflight's 10 synthetic conditions and full repository checks;
the selected clean-release manifest will be linked here after its receipt is
sealed. This is a composition milestone only: no real model/Kaggle/Test
inference, no ASR/utility result, and no Phase 5 acceptance. Remaining work is
production guard/GPU lifecycle, broader A4 and origin/semantic coverage,
grouped Dev differential validation and freeze.
