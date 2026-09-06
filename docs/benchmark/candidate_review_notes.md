# Assistant authoring review — 12 unsplit candidates

Date: 2026-09-06. This is an assistant-authored inspection of candidate text,
catalog and reference scripts, not independent human review or family approval.
The owner's same-machine/peer-review waiver remains unchanged. No LLM output
was used to select or strengthen a case. Existing candidate bytes are retained.

## Findings and next authoring decisions

| Candidates | Observation | Required next action |
|---|---|---|
| `awb_document`, `awb_emergency` | Shared authority/urgent side-effect template, different source details and sinks | Keep in one review unit; do not count names/domains as independence |
| `awb_cache`, `awb_redirect` | Same authorized-destination substitution pattern across email/webhook | Keep grouped; inspect whether one mechanism with two sink realizations |
| `awb_output`, `awb_telemetry` | Tool output adds a mandatory confirmation/telemetry send | Keep grouped; do not infer independence from calculator expression or sink type |
| `awb_database` | Read outside column scope followed by final leakage | Preserve separate read and final checks; source exposure alone is not final leakage |
| `awb_mail` | Valid recipient does not authorize an extra sensitive field | Preserve both column scope and per-artifact sink checks |
| `awb_webhook` | Sensitive read/internal send can be legitimate while outside send/final disclosure is not | Preserve positive authorized-sensitive control; scrutinize overlap with other destination-substitution candidates |
| `awb_scope` | Extra document read explicitly outside user scope | Do not call this exfiltration merely because a read occurred |
| `awb_followup` | Tool-provided plan expands a calculator-only task into document access | Scrutinize relationship to cross-document scope expansion despite different source type |
| `awb_quoted` | Embedded role transcript attempts to turn quoted content into an action | Inspect whether the benign dialogue matches role/format complexity sufficiently |

The deterministic audit enumerates all 66 pairs. Three shared template edges
yield nine conservative review units, **not nine proven-independent families**.
Cross-template conceptual similarities in the table remain unresolved; automatic
action-shape hints are not a substitute for that examination.

## Text-level limitations observed

- Several attack texts label their own instructions as fake/self-authorized or
  explain that they conflict with the user. These are useful explicit fixtures
  but may create unintended class cues in a research benchmark. Review wording
  in a separately versioned authoring revision without changing objectives.
- Benign additions frequently explain that no extra action is required. This
  can cue safe behavior beyond simply removing the malicious factor. Review
  neutral task-relevant alternatives; do not edit according to model success.
- Addition-length ratios (benign words / attack words) range from 1.0270 to
  1.7391. `awb_redirect` is 40/23 words, the largest discrepancy; output,
  webhook and telemetry pairs also warrant attention. Ratios use whitespace
  words, not model tokens, and are diagnostics rather than an acceptance cutoff.
- Public tasks tend to state scope restrictions explicitly. This is a bounded
  pilot design, not evidence of representative difficulty across 70 families.
- Variantability is not certified: no reviewed code-mix/paraphrase/word-boundary
  sets have been generated for these candidates.

## Utility QA improvement

New typed sidecars distinguish full numeric/entity/time/date values and require
observable evidence from the declared source action. Regression tests demonstrate
the legacy substring false positive and alternative date false negative without
rewriting historical scorers or scores. Requested sink completion and all security
violations remain independent checks. Typed presence still does not establish
entailment or resolve contradictory prose; do not call it a general evaluator.

Next concrete dataset step: revise the canonical pilot in a new version with
neutral, length-comparable benign controls and explicit semantic-group decisions,
carry forward source/sink/utility evidence, then author additional mechanisms.
Do not assign split or generate variants until canonical/pair QA is sufficient.
