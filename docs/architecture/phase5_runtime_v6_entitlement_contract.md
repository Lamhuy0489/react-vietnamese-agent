# Phase 5 runtime v6 — host-bound final entitlements

`security_runtime_v6_entitlement_adapter` composes the selected v5 loop with
the bounded `final_entitlement_v1` release component. It supplies the final
bound dependency through a per-call context rather than modifying
`runtime_v5.py` or copying the ReAct loop. The adapter therefore preserves the
same A0–A6 execution, Broker, warm-guard and trace lifecycle while changing
only the A6 final-release policy identity.

## Binding and composition

For A6, a host may pass a `FinalEntitlement`; its raw-user SHA-256 must equal
the task instruction before any output directory or guard worker is created.
When no entitlement is passed, the adapter extracts one from the raw user at
the final sink. Extraction failures become an empty entitlement, never an
implicit grant. The final component still requires the same run-local
`ValueOriginIndex`, exact proposal ancestry and complete observed-source
coverage. Trusted exact source/table/value-type matches remain; other protected
values are redacted or the final is denied as specified by its component.

The adapter uses a cloned function-global map for the frozen v5 body. This is a
host implementation detail: no process-global monkeypatch or cross-task cache
is used. Final decision traces identify `final_entitlement_release_v1`, and
metadata records the adapter profile, host-supplied flag and release decision;
raw user text and hidden reasoning are never written there.

## Scope and acceptance

Synthetic CPU Replay covers explicit trusted release, implicit redaction,
wrong-source and untrusted origins, normalized-only denial, public no-match,
parse terminal behavior, A0 pass-through and hash rejection. The adapter does
not change A0–A5 policy, select a production guard, access model weights,
Kaggle, benchmark Dev/Test or evaluator ground truth. Its receipt is a runtime
composition milestone only; broader A4 scope, semantic/complete origin
coverage, real guard/GPU lifecycle, grouped Dev and Phase 5 acceptance remain
open.
