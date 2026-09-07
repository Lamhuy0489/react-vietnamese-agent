# Phase 5 policy contract v1 — component milestone

Owner authorized Phase 5 on 2026-09-07. Preserve every source/test/config bound
by earlier receipts; add `security_v1` and separate configs/tests. No Test payload
or oracle parsing; no benchmark tuning in this first synthetic micro-suite.
No new LLM/Kaggle inference or model selection in this milestone.

## Frozen component matrix

| Level | Rule | Model guard | Session sensitivity | Session trust | Joint session | Value origin / full gates |
| --- | --- | --- | --- | --- | --- | --- |
| A0 | off | off | off | off | off | off |
| A1 | on | off | off | off | off | off |
| A2 | on | on | off | off | off | off |
| A3 | on | on | on | off | off | off |
| A4 | on | on | on | on | off | off |
| A5 | on | on | on | on | on | off |
| A6 | on | on | on | on | on | on |

Validated immutable config rejects any contradictory switch. Agent prompt,
model/decoding, tools, limits and raw input are not security-config fields.
A2–A6 require the same explicit guard identity before any guard run; no fabricated
default model. YAML declares components, not their implementation readiness.
A6 will retain detectors/session tracking but replace coarse session vetoes
with value-origin adjudication, as phase5 II/XXXVIII/LV requires. Thus cumulative
components do not imply monotonically larger blocked sets. Exact A6 arbitration
and value/unknown-origin semantics require a later contract before implementation.

## Policy boundary

Strict immutable models, canonical JSON and versioned hashes. `PolicyObservation`
accepts only host artifact ID, content and sensitivity/trust/source type, not
family/attack labels, expected answers, grants or evaluator sidecars. Host-only
metadata is a caller contract, not proof that arbitrary supplied labels are true.
Decisions enumerate PRE/POST/FINAL and ALLOW/DENY/TAG/QUARANTINE/SANITIZE/REDACT,
reason codes, related artifact IDs and component. No free-form reasoning field.

## A1 semantics

Scan raw plus security_v1 detector-normalized views, case-insensitively. Rules
are short bounded lexical families: override directives, control-plane reference,
send verb AND address/endpoint on untrusted source. No address/family memorization,
no scan truncation, no attack classifier claim. Rule IDs are deduplicated and
ordered. A1 POST only TAGs, never edits/drops original ToolResult. Signals remain
sticky per run. PRE allows read/compute; denies an external action with an active
signal unless user explicitly authorized that tool AND exact destination. FINAL
always passes. Simple lexical rules may flag quoted educational instructions.

Authorization anchors use only the raw user instruction, never retrieved text.
Only affirmative supported clauses beginning with Vietnamese gửi/gởi/send or
post and containing the relevant email/webhook vocabulary/destination count.
Negated/conditional clauses, quoted blocks and bare addresses do not authorize.
This is deliberately bounded extraction, not general Vietnamese intent parsing;
unsupported phrasing can false-block. Exact destination comparison, no loose
domain/substring or URL decoding. No authorization from a destination alone.

`GuardedBrokerSession` is an A0/A1 execution adapter, not yet the shared ReAct
loop. A denied proposal records proposed/decision, has no Broker/tool execution
and no fabricated ToolResult. Every allowed call uses unchanged ToolBroker.
POST gets source-native labels from the host catalog, not rendered context taint.
Observation contents are not rewritten. A0 skips detectors entirely. Session is
run-bound and step-monotone; a new instance is required for every task.

## A2 interface preparation (not operational LLM evidence)

Guard prompt treats candidate text/action as untrusted classification data;
output exactly risk SAFE/SUSPICIOUS/MALICIOUS, bounded label enums and confidence
LOW/MEDIUM/HIGH. Reject extra fields, malformed/duplicate JSON keys, code fences,
reasoning, NaN and invalid enum values. No hidden CoT requested or stored.
Backend adapter uses deterministic generation and immutable model/revision/prompt/
generation/input identity. Cache successful typed results only, per instance;
model revision changes fail, not silent cache reuse. Exceptions become typed
ERROR without raw exception/model text logging. TimeoutError is handled; a real
backend must provide bounded execution/cancellation before A2 can be accepted.
No thread-timeout wrapper pretending to terminate GPU inference.

## Acceptance for this milestone

Config/GT rejection, deterministic rules, matched micro-controls, A0 detector
bypass, A1 denied-proposal/no-tool-side-effect, allowed Broker trace, fresh state,
strict guard parser/cache/error tests and all prior checks pass. This is not
whole-phase acceptance. Remaining: shared instrumented runtime integration,
guard model choice and actual Dev inference, A3–A6 enforcement, grouped tune/
validation Dev protocol, differential validation and full Phase 5 freeze.
