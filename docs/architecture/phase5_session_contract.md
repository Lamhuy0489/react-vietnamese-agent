# Phase 5 session policy contract v1

Scope: A3–A5 integration on new source only. Preserve selected A0/A1/A2 source,
rules, guard prompt/parser/config and all sealed inputs. No Dev tuning, Test
payload access or real-model quality claim. Plan sections XXIV–XXXVI apply.

## Predeclared cumulative interpretation

The frozen research contract/config matrix takes precedence over plan shorthand:
A4 retains A3 sensitivity, and A5 retains A1–A4. Do not silently create standalone
sensitivity-only/trust-only ablations under these cumulative names.

- Initial state S0, no observed sources or alerts; raw user is authorization input,
  not a retrieved source that automatically taints every session.
- Post joins host source sensitivity by max(S0,S1,S2); lower later sources cannot
  downgrade it. Trust is a separate OR of observed UNTRUSTED labels. No inference
  from sensitivity to trust or vice versa. Labels come only from SourceCatalog,
  not content assertions or evaluator ground truth. Failed-tool source snapshots
  keep host labels conservatively, as in the existing runtime.
- A3: deny external email/webhook if session sensitivity exceeds S0 clearance.
  Authorization does not declassify. Reads and final remain pass-through; this
  deliberately overblocks unrelated S0 output after an S1/S2 read.
- A4: additionally deny an external action after any untrusted source unless
  the existing raw-user-only, action-specific destination anchors authorize it.
  Rule/guard alerts from an untrusted source also set an observable control flag;
  A4's coarse veto uses untrusted_seen, not a claim of exact action derivation.
  No general processing-scope/ID parser is claimed by this bounded implementation.
- A5: additionally deny external action if any rule alert, LLM SUSPICIOUS or
  MALICIOUS alert, or detector/guard error has occurred in this task. This includes
  the current action's guard result, before execution. A later SAFE result cannot
  clear a signal; explicit authorization cannot override this joint veto. Thus
  SUSPICIOUS remains TAG-only in A2–A4, but is a predeclared coarse veto in A5.
- Earlier A1/A2 denials are never relaxed. One policy/guard/cache/state per task;
  no detailed body provenance, value matching, sanitization or final protection
  before A6. A6 still rejects explicitly.

## Evidence and runtime boundary

Immutable typed session snapshots record initial, Pre, Post and Final state,
candidate/proposal IDs and related alert/source artifact IDs. Model context is
unchanged except the existing generic denial feedback. Session metadata and
guard sidecars are not model inputs. A0–A2 retain observable parity.

The new runtime creates empty guard/session sidecars for zero-call runs when
enabled. Guard backend remains the A2 cold spawned-process adapter; production
guard identity and an efficient GPU lifecycle are still pending, not simulated.

Acceptance: independent synthetic label/authorization/alert matrix; monotone
state, fresh runs, cumulative vetoes, both external sinks, repeated denials,
zero-call terminal paths, exact A0/A1/A2 parity, source/artifact trace audit,
sealed-input hash checks, setup/lint/typing/full tests and knowledge validation.
