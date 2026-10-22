# Phase 5 acceptance review — proposal for owner review

Date: 2026-10-02. Scope: read-only inspection of the approved Word plan, research
contract, Phase 5 DoD, current source and saved receipts. No inference, notebook
submission, runtime edit, Test payload inspection or acceptance change. External
web search was unavailable (tool service HTTP 404); findings below are grounded
in local primary project documents/code, not newly verified literature.

## Finding

The original phase is implementation and bounded smoke verification of A0–A6,
followed by a source/config freeze. The Word plan assigns the general evaluator
to weeks15–16 and final experiments to weeks17–20. Phase 5 does not require A6 to
win every metric, achieve an unspecified global ASR/FPR threshold, or solve
arbitrary semantic provenance. It does require correct representative benign
behavior and the specified sensitive-egress/final/unknown-origin controls.
Recorded operational gates must be reconciled explicitly, not silently removed.
The 2026-09-29 decision already says native GPU cancellation is not a new DoD.

## Verified evidence and limits

- QA receipt:213 passed on four test modules. All358 source hashes and four test
  hashes still match current files. This was hash verification, not a new pytest run.
- Native current epoch:16 terminal checkpoints =15 normal completions +1 network
  failure;68 conditions never started. Five partial-receipt dependency hashes match.
- C1 read public and C2 email public exercised all seven levels; C3 webhook public
  only A0 completed normally. No native current-epoch private/unknown-origin/A6
  public-after-private contrast has yet been observed.
- CPU04 historically reports84/84 and44/44 required control rows. That is Replay
  with synthetic guard, not a live guard classifier result. This review read the
  report; it did not revalidate the entire historical CPU04 artifact inventory.
- Current readiness code deliberately emits20 open DoD and accepted=false.
  Historical formal-freeze code is explicitly a NO_GO validator. Neither is a
  complete evidence-based acceptance decision engine; successful model runs alone
  cannot make these reporters accept the phase. Preserve historical receipts.

## Twenty-criterion evidence map

Status below distinguishes observed evidence from missing release admission;
it does not declare any formal DoD accepted.

| DoD | Original requirement | Evidence now and remaining action |
|---|---|---|
|1|Seven configurations on common runtime|Common v14 entrypoint and seven native public-read/email levels exist; bind final integrated release and regression evidence.|
|2|Config isolation|Manifest pins and snapshots exist; explicitly compare model/data/tools/environment/decoding and common prompt mechanics across levels.|
|3|A0 parity|Current source-bound QA includes20 Phase4-versus-closure Replay tasks and model-message comparison; retain as direct evidence, not reset to missing.|
|4|A1 operational|Current tests cover rule attack/benign contrasts; bind exact candidate paths and observable decisions.|
|5|A2 operational|30 native guard attempts in partial epoch, synthetic fallback tests; audit actual responses, both benign/attack guard behavior, malformed/timeout/API errors in integrated path. SAFE counts are not accuracy.|
|6|A3 sensitivity|Historical CPU controls and current private-egress unit contrast; bind complete source-matched session sensitivity controls.|
|7|A4 trust/anchors|Historical deterministic destination controls; source-matched untrusted redirect and authorized-recipient contrasts needed in release dossier.|
|8|A5 session combination|Historical session controls; verify sensitivity and trust separately and jointly with logged decisions.|
|9|A6 artifact awareness|Current C7 CPU permits public-after-private; native corresponding contrast pending. Include sensitive payload negative pair.|
|10|PRE before external dispatch|Native benign traces show PRE/Broker ordering; complete deny/error/bypass checks on candidate.|
|11|POST before context|Benign traces show POST; bind negative/error and actual model-context checks, not merely event presence.|
|12|Every released final gated|Normal native paths have final events; verify parse/model/max-step error paths cannot release unfiltered text. No answer on infrastructure failure is not itself leakage.|
|13|S2 email/webhook protection|Historical deterministic controls pass; bind current exact source and both sinks. Native pending; baseline lower levels may remain vulnerable by design.|
|14|Known sensitive final redacted/denied|Current C10 Replay check passes; actual-model path and intended final representations remain bounded evidence to finish.|
|15|Representative benign utility|Native public read/email positive evidence exists; add representative webhook and public-after-private controls, document false blocks. One literal is not representative of every task.|
|16|Unknown critical lineage denied|Historical C9 control; bind current candidate and ensure real unknown input, not fabricated provenance.|
|17|Policy/evaluator separation|Current QA includes rejected evaluator fields and input isolation; audit runtime/worker prompt boundaries for release.|
|18|Sealed Test hashes unchanged|No new hash-only seal comparison performed in this review; required before acceptance. Do not parse Test payloads.|
|19|No real side effects|Native tools are mocks; bind direct socket/SMTP/HTTP interdiction evidence for actual integrated registry.|
|20|Freeze architecture/config/rules/guard|Worker releases committed; host contains working-tree source. Need coherent selected host release plus rules/prompts/configs/models, tests, hashes and20DoD decision.|

## Two audit issues to correct before using it for acceptance

1. `scripts/evaluate_phase5_acceptance_v1.py` sets all DoD open and accepted=false
   unconditionally. Keep it as historical readiness or add a separate versioned
   final acceptance audit that consumes explicit per-DoD admissible evidence.
   Never replace the boolean with true without implementing those checks.
2. Native observation reporting distinguishes not_exercised, but its nested
   readiness still requires the deterministic control matrix to pass. The
   deterministic DENY check requires an actual proposal. A model that never
   proposes the unsafe action lacks gate-exercise coverage; it has not thereby
   demonstrated a security violation. Separate policy controls, native behavior,
   and overall DoD decisions. Similarly no final after network failure is an
   incomplete execution, not proof of a FinalGate bypass.

## Proposed finite order, not authorized implementation

1. Freeze a concise20DoD evidence contract and explicit pass/fail/missing rules.
   Reuse verified parity/components/fallback evidence. Mark historical versus
   current source. Do not invent new numerical model-performance thresholds.
2. Small infrastructure repair: reconcile transport uncertainty without deleting
   old journals, silently retrying semantic outcomes, or changing model/policy.
   HTTP404 REQUEST_UNKNOWN alone is not a durable terminal receipt. Prove safe
   non-admission or close the old worker/attempt with auditable disposition; if
   identity/source changes, declare the deviation and continuation scope. A new
   epoch is permissible only with that explicit accounting, not to hide failure.
3. Source-matched deterministic coverage first, then the missing native schedule
   under the already frozen protocol or an explicit prospective amendment. Keep
   all failures and denominators. Add separately declared direct guard benign/
   attack and fault checks where the84-case matrix cannot exercise them.
4. Acceptance audit: all mandatory smoke/invariants pass, representative benign
   controls work, failures classified, held-out seals intact, release sources and
   configs frozen. Then update phase status; general statistics remain Phase6/7.

Architecture recommendation: keep local orchestration/Tool Broker and the two
Kaggle inference workers. No local GPU needed. Do not redesign A6 yet; pursue a
bounded root correction only if source-bound representative controls fail.
Request tracking is supporting infrastructure, not the research contribution.

## References

- [Original DoD](../../plan/phase5.md#cxxvi-definition-of-done--phase-5)
- [Research contract](../project/research_contract.md)
- [2026-09-29 explicit decisions](../project/decision_log.md)
- [Current partial audit](phase5_public_guard_partial_20261002.md)
- [Current QA receipt](../../build/evaluation/phase5_public_guard_host_qa_20261002.json)
- [Historical CPU root-fix report](phase5_root_fix_20260929.md)
- [Readiness implementation](../../scripts/evaluate_phase5_acceptance_v1.py)
- [Historical NO_GO freeze implementation](../../src/react_agent/validation/phase5_formal_freeze_v1.py)

Owner requested explanation before changes. This proposal does not approve or
implement a revised protocol, new experiment, or phase promotion.
