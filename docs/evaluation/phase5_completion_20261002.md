# Phase 5 closure dossier — 2026-10-02

Owner requested execution of the independent-review recommendations to finish
Phase5. This dossier binds the existing implementation release and fresh checks.
**Phase5 accepted for bounded implementation and smoke verification on2026-10-02.**
All20DoD passed the final audit after the guard diagnostic finished. No Phase6/7 execution or Test inference is authorized here.

## Accepted scope and evidence

The normative requirements are the20DoD in plan/phase5.md, operationalized by
[evidence contract v2](phase5_acceptance_contract_v2.md). Implementation source
is `419938b4c2bc9842a92b2d797126d69ae727c953`; it preserves cumulative A0–A6,
host Tool Broker, independent sensitivity/trust, source labels and FinalGate.
The new diagnostic scripts do not change runtime, worker, policy or guard prompt.

Fresh verification: setup/Ruff/mypy pass;450 closure regression tests pass
(178.52s), plus17 new failure-code/guard-runner tests pass.80 synthetic constant
guard executions and missing-only resume0 validate the exact diagnostic runner;
they are not real-model quality measurements. Full repository pytest was not
rerun: historical authoring suites include sealed construction data; focused
scope covers the accepted runtime, faults, recovery and new scripts.

The offline acceptance audit revalidates source inventories, snapshots,
configurations, artifact hashes, QA receipts, committed release bytes and
hash-only sealed assets. It reproduces20PASS. All12native errors remain in the
84-condition denominator. Original checkpoints and historical receipts remain
unchanged. Old NO_GO/readiness receipts describe their original stage, not the
current release decision.

| DoD | Direct evidence in the release dossier |
|---|---|
|1 Seven levels|CPU84 common runtime and native C1 completed at all A0–A6|
|2 Isolation|Matching CPU/native manifests, source/config/model identities and cumulative-config tests|
|3 A0 parity|20 Phase4-versus-closure Replay tasks, observable behavior and model-message checks|
|4 A1|Rule attack/benign micro-controls and integrated level contrasts|
|5 A2|Native guard structured responses, benign/hostile observations, strict parser and error fallback tests|
|6 A3|CPU private-egress sensitivity controls|
|7 A4|CPU untrusted-destination controls and raw-user anchor tests|
|8 A5|Independent sensitivity/trust matrix and combined-session decisions|
|9 A6|C7 native public-after-private email ALLOW; C8 sensitive-payload PRE DENY; CPU contrasts|
|10 PRE|Proposal/PRE/Broker joins, denied-proposal exclusion and bypass tests|
|11 POST|Ordered tool-result/PostGate checks and actual context-view tests|
|12 FINAL|Gated released finals; parse/model/max-step failures release no unfiltered answer|
|13 Sensitive sinks|Both email and webhook negative controls, A6 no unsafe dispatch|
|14 Known-secret final|C10/A6 REDACT plus deterministic final controls|
|15 Benign utility|A6 public read/email/webhook and public-after-private actual values/destinations|
|16 Unknown lineage|CPU/native unknown-critical-source rejection with an actual denied proposal|
|17 Oracle separation|Schema rejects evaluator fields; context/input separation tests|
|18 Test integrity|Hash-only checks against committed clean/adversarial seals, zero payload deserialization|
|19 Mock side effects|Integrated mock registry runs with socket/SMTP/HTTP interdicted|
|20 Freeze|Pinned runtime/config/rules/prompts/model/worker identities, committed release and verified QA receipts|

The executable decision is
[historical20PASS receipt](../../experiments/manifests/phase5_acceptance_20261002.json),
rechecked at `build/evaluation/phase5_completion_20261002_01/acceptance_recheck.json`.
The table is an explanation of that audit, not an independent substitute for it.

## Recommendation steps carried out

1. **Baseline and acceptance:** retained the source freeze, ran current regression
   and acceptance checks, and assembled this dossier. No84-case rerun.
2. **422 diagnosis:** exact source-defined error envelopes match the saved hashes
   for all11requests as `OUTPUT_SCHEMA_FAILED`; none matches `OUTPUT_LIMIT`.
   See [failure-code receipt](../../experiments/manifests/phase5_failure_codes_20261002.json)
   and [auditor](../../scripts/audit_phase5_failure_codes_v1.py). Real worker
   envelope tests cover both known codes, unknown response, altered hashes and
   identity mismatch. This identifies the error code, not why a particular
   generated JSON failed; no unsupported timeout/token change was made.
3. **Guard quality:** a separate prospective80-request Dev diagnostic uses the
   existing pinned worker and frozen guard interface. All40Dev families, one
   matched pair each; eight pairs per variant. Protocol and hashes precede
   inference. See [protocol](phase5_guard_quality_v1_protocol.md); terminal
   results:TP21,FN19,FP5,TN35;80/80valid,0errors,0duplicates.
   [Guard terminal report](phase5_guard_quality_v1_report.md) and the final
   completion receipt preserve the two GET-only interruptions and admission amendment. Labels never enter
   run() or the worker. Quality findings do not retroactively alter20DoD.
4. **C6 policy:** kept as an explicit conservative-composition limitation. A6
   inherits SESSION_COMBINED_RISK even when the observed proposed email is
   authorized and public. No removal of vetoes or expanded permission was
   needed to satisfy the original representative benign controls. A future
   policy improvement requires a versioned host-proof design and paired unsafe
   controls, not editing this accepted run.

## Boundaries that survive acceptance

- Native closure:72completed/12model_error across84scheduled conditions.
  Completed means runtime termination, not utility. A0–A2 carry the12errors;
  completion-rate differences cannot establish a defense ranking.
- A6 has bounded observable value-origin evidence, not causal semantic lineage
  for arbitrary model text. Literal/typed/whole-value encoding checks have
  declared limits and collision trade-offs.
- 217 closure guard verdicts are not classifier accuracy. The new paired Dev
  diagnostic is not ASR, an independent Test evaluation or proof of all
  PRE/POST/FINAL behavior. Reused Dev families may share conservative groups.
- C6 false blocking remains real; lower-level vulnerabilities remain expected
  baseline observations. A6 does not need to win every metric to satisfy the
  implementation phase.
- Host process cleanup does not prove remote GPU shutdown. Health is observed
  at admission, not an uptime guarantee. No notebook was submitted for closure.
- Review remains owner-authorized automated/assistant verification under the
  recorded waiver; do not describe it as independent human peer review.
- Raw evidence remains local under build/. Git source and receipt hashes do
  not imply remote backup of raw data or credentials. No secret connection file
  belongs in a release package.

After closure, Phase6 evaluation framework and Phase7 final experiments remain
separate phases. Their expected work is not reopened as missing Phase5DoD.
