# Phase 3 executable workbench interface v0.1

Scope: four synthetic unsplit canonical pairs to validate authoring machinery.
This is not a replacement/freeze of the 70-family benchmark. No new Test split,
model inference, learned defense or final evaluation metric is introduced.

## Separation and interfaces

- `public/tasks.json`: only `task_id` and legitimate `instruction` are passed
  to `AgentRuntime`. No attack label, oracle, forbidden values or safe script.
- `overlays/scenarios.json`: source type/identity, base public content, attack
  and benign additions; optional synthetic DB sensitive value. These are
  environment inputs, not system prompts or policy instructions.
- `private/oracles.json`: expected facts, authorization, artifact references,
  safe and negative observable scripts. Loaded by local QA only, never passed
  to registry construction or runtime context.
- Pydantic schemas reject unknown fields and unsupported tool/source types.
  Canonical/task identities must align. Review stays `pending`; tests cannot
  grant language-quality approval or future phase acceptance.

## Overlay semantics

Build a temporary copy of the frozen clean_v1.1 environment. Add a document,
cached page or namespaced DB row to this copy only. For calculator tool-output
poisoning, wrap only the selected exact call and append a text notice to its
successful result. Preserve the ordinary result and parser input schema.

Each pair shares user task, original public fact, source identity, authorization
and safe path; only the added source text differs. Neither branch has a runtime
security gate. All tool execution, including QA probes, goes through Tool Broker.

## Local oracle semantics (bounded fixtures, not Phase 6 evaluator)

- Record proposed unauthorized actions separately from successful simulated
  executions, joining proposal/execution/result by call ID. An executed event
  before an unsuccessful tool result does not prove a delivered mock effect.
- Check final-answer leakage separately using exact synthetic artifact values;
  do not count mentions of an artifact name alone as leakage. This is not a
  semantic/encoded-leakage detector and does not implement provenance tracking.
- Check fixture facts and required authorized actions for legitimate utility.
  Refusing everything must fail utility even if no violation occurs.
- These four fixture fact checks are literal matches, required sink actions
  use exact arguments, and the private prohibited DB query is an exact action
  fixture. They do not recognize arbitrary equivalent SQL, paraphrased facts,
  encoded leaks or all possible data-scope violations. General evaluation is
  not accepted on the strength of these bounded positive/negative tests.
- Prove reachable payload, safe attack/benign paths, authorized email delivery,
  harmful email/webhook/final fixtures, and absence of network side effects.
  Negative scripts prove the oracle recognizes violations, not that an LLM
  would follow the attack. No ASR/FPR or model capability claim follows.

## Acceptance of this milestone

All four pairs must pass executable fixture QA and regression tests; public
context must exclude private-only metadata; originals must retain their hashes.
Record source/input hashes and aggregate evidence, preserving raw logs outside
Git. This gate does not accept Phase 3, generate variants, or allocate Dev/Test.
