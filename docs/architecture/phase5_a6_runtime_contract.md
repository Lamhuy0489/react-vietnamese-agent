# A6 runtime v4 — bounded integration contract

Predeclared integration of frozen value-origin, PreGate, Post-view and final
release components. Phase 5 only; synthetic Replay and fake process guard QA,
no benchmark/Test payloads or model-quality claims. All prior selected source
is immutable. One new config-driven loop supports A0–A6; historical loops stay
as reproducibility references, not separate per-level implementations.

## Composition

A0–A5 retain v3 behavior, raw contexts and final pass-through. A6 requires the
same explicit process-owned guard identity as A2–A5. It collects the complete
A5 coarse verdict and session state, then runs the host-bound value gate.
Only the pair SENSITIVITY_EXCEEDS_SINK_CLEARANCE / SESSION_SENSITIVITY_RISK
may be discharged when the value gate ALLOWs with complete exposed-source
coverage. Any other coarse reason still denies an external action. A value DENY
cannot be overridden by guards or user anchors. Preserve coarse and value
decisions separately in a versioned host-only trace. This implements plan II/LV:
cumulative components do not imply cumulative blocked sets. No A5 risk veto
is silently removed and no source label is downgraded.

## Source/context lifecycle

Create one origin index per run; admit only raw host user and actual tool-source
snapshot roots at their observation step. Failed admission leaves the index
incomplete, recorded with error class only: reads may continue, external/final
release fail closed. Never index generated actions, views or policy feedback.
PreGate proposal parents descend from the exact context used by the backend.
After every executed tool, existing raw Post handling, rule/LLM scanning and
session updates run first. An untrusted Post view is a derived JSON envelope;
the next model context references that view artifact, not the raw observation.
Trusted observations stay byte-identical. No tool executes except via Broker
after the composed PRE decision. Schema/integrity failures abort before execution.

## Final sink

Fixed host policy `a6_public_final_v1`: final clearance S0, independent of user
text, source instructions and evaluator ground truth. This is deliberately
restrictive; private-record entitlements are NOT implemented or inferred.
Verify complete two-way observed-root/proposal-ancestry coverage, then invoke
the frozen deterministic release component. Coverage failure produces a new
empty released artifact and DENY. Known raw protected values redact; normalized
only/scan failures deny. Every A6 parsed final has separate proposed/released
artifacts, hashes and final decision; return/log ONLY released text in the final
answer field. Proposed text remains in observable model/artifact audit logs.
No second LLM generation. Existing terminal `completed` means loop termination,
not security success; metadata separately records final effect and release ID.

Index, release decisions and policy snapshots are host-only and never injected
into benchmark prompts. Model context changes only through declared Post views.
Missing origin for external critical fields fails closed. Final no-match means
no match under the finite frozen extraction profile, not semantic proof: short
names, arbitrary paraphrase, encoding and SQL aliases remain limitations.
Case-changing an email is also outside the case-sensitive matching profile.

## Acceptance and remaining work

Test A0–A5 parity, A5/A6 unrelated-S2 differential, both external sinks, all
sensitivity/trust dimensions, guard/rule vetoes, unauthorized/unknown fields,
actual Post context identity, final ALLOW/REDACT/DENY, error/parse/max-step
terminal paths, run isolation, hash/trace reconstruction and offline tools.
Run setup/Ruff/mypy/full pytest and sealed-input/prior-source hash checks.
Runtime integration does not close Phase 5: production guard/GPU lifecycle,
general A4 scope, grouped Dev validation and policy freeze remain pending.
