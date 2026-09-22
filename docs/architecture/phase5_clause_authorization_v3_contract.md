# Phase5 — clause authorization candidate v3 / runtime v12

2026-09-21. Opt-in CPU candidate, not a native worker release or Phase5 acceptance.
Inputs are the unchanged raw public user instruction and host-labeled artifacts.
No benchmark expectations, evaluator ground truth, tool instructions, memory or
model output may grant authority. Frozen v1/v2 parsers and measured runtimes stay intact.

## Bounded grammar and conservative limits

- Record immutable clause offsets into the original string and its SHA-256.
  Recognize sentence punctuation, semicolons/newlines and a comma before a send
  directive; never normalize user text to create a grant.
- Admit explicit read-ID lists, bounded field/table reads and current-source
  selection prefixes before send directives. Resource identifiers retain case.
  Unsupported preceding prose prevents a subsequent send grant.
- Recognize direct send-to email, webhook-to endpoint and direct endpoint plus
  payload directives. Validate whole destination tokens; a URL-path suffix must
  not become a shorter email grant. Destination authority is not payload clearance.
- Fail closed for any quotation marker, reported-instruction cue or conditional
  in the instruction. This deliberately rejects some otherwise valid quoted or
  conditional tasks; it is not a full Vietnamese/English language parser.
- Any unscoped send prohibition or explicit cancellation revokes all destination
  grants regardless of order. A narrow named-resource sentence such as
  `Mã đối soát DOC_002 chỉ được đọc, không được gửi hoặc đưa vào câu trả lời`
  is a payload prohibition, not revocation of another public payload's destination.
  Other payload-prohibition forms can be conservatively denied; no general semantic
  per-field permission engine is claimed.
- `nội dung` must not be mistaken for the unaccented negation `dung`.
  An `example.test` domain must not be mistaken for reported prose `example`.

## Cumulative integration and provenance

`runtime_v12` delegates A0 to frozen v10 without authorization metadata changes.
A1–A6 use the same clause parser through an inheritance hierarchy preserving
the runtime's A2/session/A6 type checks. A6's coarse and value gates share it.
Private function bindings do not mutate imported module globals or rewrite the
raw task sent to the agent/guard. Scope v5, SQL rows, guard errors, sticky vetoes,
sensitivity checks and final-answer gates remain in force.

The new `host_destination_origin_v3` index supplements only literal email/URL
destinations in an admitted raw host-user root. This addresses an email followed
by sentence-final punctuation missing from the old extraction profile. It keeps
the source's exact ID, content hash, sensitivity and trust, deduplicates records
and checks existing count/byte budgets. Tool/model roots never get this extra
authority; arbitrary payload fields still require their own origins. It does not
repair every punctuation boundary in the older general-purpose extractor.

## Validation and release boundary

Run the fixed 26 synthetic controls in semicolon, sentence and compound forms:
78 executions, fresh environment/run state each. Keep all outcomes, including
failures; never overwrite a previous directory. Record source hashes before and
after execution, raw traces, actual broker dispatch, final gate and input hashes.
Six destination-bearing public Dev fixtures in the unchanged 16-fixture paired
selection are checked for destination recognition only, not benchmark success.

Before native dispatch: bind this runtime/index/parser into the constrained
ExitPair path, update independent receipt audits and runtime identities, validate
both package layouts and freeze the exact worker source. A CPU pass does not
authorize calling the old native runner a v12 run. Native quality/utility,
lifecycle reliability and formal acceptance remain separate gates.
