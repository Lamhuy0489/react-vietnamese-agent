# Security Architecture

| Level | Cumulative addition |
|---|---|
| A0 | Baseline schema validation and bounded tools only |
| A1 | Rule/regex guard |
| A2 | Model-based guard |
| A3 | Data-sensitivity control |
| A4 | Untrusted-data/control-influence tracking |
| A5 | Session-level sensitivity + trust policy |
| A6 | Artifact provenance with Pre/Post/Final gates |

A0 purity is required for an interpretable baseline. A6 is the central
technical contribution, but provenance is conservative evidence tracking—not
a claim that the system perfectly knows which text influenced the model.

## A6 v2: value provenance refines session vetoes (rebuild R2, 2026-10-26)

A3–A5 decide per session: once a session has read sensitive or untrusted data,
every later external sink call is denied. That is safe but over-blocks: on the
Dev reference replay A4–A5 keep 20/200 benign tasks. A6 keeps all A1–A5
components and adds per-value evidence for **external sink calls**
(`security_v1/a6_provenance_v2.py`):

1. **Destination.** Granted when the exact address or endpoint is written in
   the raw user instruction, outside negated, conditional ("nếu"; temporal "sau
   khi" is not conditional), reported or quoted text, or when the Phase 5 anchor
   grammar grants it.
2. **Payload values.** Every value sent must be written by the user
   (word-bounded match in the instruction) or be a calculator result whose every
   operand the user wrote. Values from tool sources never qualify, trusted or
   not: trust labels are independent of safety, and an injected value can sit in
   a trusted page. A flag counts as user-stated only next to its own field name.
3. **Discharge.** When steps 1–2 prove the call and nothing sensitive is in the
   payload, the coarse session vetoes (sensitivity, trust, control influence)
   are discharged. A1 rule and A2 guard reasons still veto, and a sensitive
   payload or untrusted destination is never overridden. Reads keep the Phase 5
   resource-scope decisions.

Dev reference replay (guard fixed to SAFE): benign utility A5 20/200, Phase 5
A6 20/200, A6 v2 115/200; reference attack harm stays 5/200 with no newly
harmful variant. Known limit: a value the model must copy from an untrusted
document (for example a quantity read from a page) is still blocked; recovering
it needs a quarantined extractor in the style of CaMeL, which is out of scope.
The Phase 5 A6 contract (`phase5_a6_runtime_contract.md`) remains the historical
baseline.
