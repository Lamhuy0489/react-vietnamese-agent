# Phase 5 — opt-in dated-room ticket, synthetic CPU ablation

2026-09-23. This versioned candidate extends only the room **data grammar**;
it does not change frozen v12 or earlier v13. The v13 ticket accepts one
complete line, `Phòng hiện hành: CODE`. The new
[`public_field_ticket_v2.py`](../../src/react_agent/security_v1/public_field_ticket_v2.py)
also accepts exactly two lines, with `Cập nhật: YYYY-MM-DD` second and a valid
calendar date. The source must still be an admitted S0 document with the same
size/provenance checks. A third line, duplicate room, malformed date, JSON,
CRLF, zero-width suffix or arbitrary prose fails closed. The v1 single-line
form is unchanged.

[`runtime_v14_dated_room_v1.py`](../../src/react_agent/security_v1/runtime_v14_dated_room_v1.py)
is a separate opt-in A6 CPU wrapper. It reuses v13's synthetic replay/guard/
eight-tool admission, v12's complete baseline PRE decision and all Broker,
POST and Final gates. Only the ticket extractor, profile and runtime identity
are substituted task-locally. The trace still records baseline and candidate
decisions; metadata remains `host_inventory_attested=false` and
`synthetic_cpu_candidate_only`. This is not a native model path.

## Paired deterministic evidence

The [new synthetic inventory](phase5_room_synthetic_inventory_v1_report.md)
fixes the same task, agent responses and host labels across branches. For a
dated public room with unrelated S2 source, v13 DENY becomes v14 ALLOW at
the authorized mock webhook. Invalid dates, appended instructions, duplicate
room lines and a value also found in the S2 source remain DENY. Separate
controls show single-line v13/v14 parity, PRE/POST malicious guard vetoes,
wrong destination denial and private-value final redaction/denial. Component
tests also reject Unicode/format ambiguities. These are Replay outcomes, not
measured model utility, ASR or a formal DoD gain.

The earlier v13 poison failure (JSON-escaped source text) remains documented;
v14 likewise requires the **entire** content to match its bounded grammar,
so it does not rely on that lexical detector to reject added instructions.
This grammar covers only one field and one optional timestamp; it does not
prove general typed origin, semantic paraphrase safety or host label truth.
The unreviewed future-ID inventory remains content-free pending owner review,
and no existing scored Dev/Test artifact is relabeled or rerun.

Local QA: 127 related tests pass, including unchanged v12/v13 controls;
setup, repository-wide Ruff, mypy on 511 source files, knowledge-check and
diff-check pass. Full pytest is outside this active slice because sealed Test
authoring tests are excluded. No model/GPU/Kaggle/real sink, source freeze or
commit is claimed. Formal Phase 5 remains 4/7 (~57%).
