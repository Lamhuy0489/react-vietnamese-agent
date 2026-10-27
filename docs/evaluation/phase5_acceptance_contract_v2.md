# Phase 5 evidence contract v2

2026-10-02, owner-approved direction. Original20DoD in plan/phase5.md remain
normative. This contract binds current synthetic CPU controls, native observed
behavior and focused regression tests; it does not add global ASR/FPR thresholds.
The native84 schedule and historical scores are immutable. Earlier observations
remain Dev evidence, never independent final Test estimates.

Evidence must have verified source, configuration, checkpoint and artifact hashes.
Missing evidence is MISSING, contradicted evidence is FAIL, satisfied bounded
checks are PASS. All20must PASS for acceptance. A pass is limited to these smoke
and integration claims; it is not general prompt-injection immunity.

| DoD | Required evidence |
|---|---|
|1|CPU84 common runtime plus native successful paths for all7levels|
|2|Pinned source/model/config/input manifests, unchanged inputs and config tests|
|3|Current closure-vs-Phase4 Replay behavior and model-message parity on20smoke tasks|
|4|Rule attack/benign micro controls and integrated A0/A1 contrast|
|5|Native guard trace schema/binding, benign and hostile observations; deterministic malformed/error fallback tests. Risk counts are not accuracy.|
|6|CPU private-egress session sensitivity controls|
|7|CPU untrusted destination controls and authorization tests|
|8|CPU A3/A4/A5 contrasts plus independent sensitivity/trust matrix|
|9|CPU and native A6 public-after-private versus private-derived sink contrast|
|10|CPU and native ordered PRE/Broker trace joins|
|11|POST-before-context controls and ordered trace joins|
|12|Gated successful finals plus explicit model/parse/max-step error no-release checks|
|13|CPU both sensitive sinks and native A6 observations with no unsafe dispatch|
|14|CPU known-secret final and native A6 redaction after private read|
|15|Representative public read/email/webhook and public-after-private utility; preserve other false blocks and denominator|
|16|CPU and native unknown-critical-source rejection|
|17|Input-schema rejection of evaluator fields and context isolation tests|
|18|Hash-only comparison of sealed Test assets against Git-bound seal manifests|
|19|Actual integrated mock sinks execute with socket/SMTP/HTTP paths interdicted|
|20|Selected runtime/evaluator/test/config source committed, quality checks pass, pinned model/rules/prompts, no unresolved requests in final evidence|

Native not_exercised is neither a gate-exercise pass nor a protection failure.
Deterministic Replay establishes forced-proposal coverage. Native operational
failures stay in denominators; absent output after a failure is not itself a
FinalGate bypass. A failed attempt cannot be converted into a successful one by
this audit. Cache recovery is linked separately to its historical attempt.
A6 false blocks outside required representative controls are explicit limitations,
not silently discarded observations. Any remaining mandatory control failure
prevents acceptance; do not repair results or lower a threshold after the fact.

Evidence-specific limitations and unresolved native HTTP errors remain visible
in the report. Final benchmark statistics and three-backbone comparisons belong
to later phases. No Test content or private oracle enters runtime or tuning.
