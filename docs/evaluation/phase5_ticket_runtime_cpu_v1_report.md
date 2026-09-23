# Phase 5 — opt-in A6 public-field ticket, CPU integration

2026-09-23. This is a **new synthetic ablation**, not a patch to frozen A6 v12
or a rerun/rescore of Dev32. Source is
[`runtime_v13_ticket_v1.py`](../../src/react_agent/security_v1/runtime_v13_ticket_v1.py);
the paired CPU controls are
[`test_public_field_ticket_runtime_v1.py`](../../tests/integration/test_public_field_ticket_runtime_v1.py).
The source/catalog labels are chosen when constructing each synthetic case,
before agent responses or outcomes. No released Dev/Test fixture is relabeled.

The v13 wrapper accepts only explicit A6 plus a versioned host annotation
catalog. A preflight also pins the agent to the built-in replay classes and
identity, the guard to `SyntheticGuardFactory` with its synthetic warm identity,
and the registry to the exact eight built-in tool classes (including both mock
egress sinks). This check happens before a worker or output directory is
created; the private task entry rejects a substituted worker too. It is an
accidental-deployment gate, **not** proof that the file-backed source content
is synthetic, that the host labels are correct, or a security sandbox against
Python object mutation. It delegates the existing v12/V7/V5 loop, guard, scope, POST, Final
and Broker unchanged. Its policy first computes the complete v12 PRE verdict;
the ticket path can reconsider only the unsupported `room` value and an
**explained** coarse S2-session veto. Any other coarse reason, guard/rule veto,
sensitive match, missing/ambiguous ticket or wrong user grant preserves DENY.
Ticket issuance also checks the exact `doc_read` action parent and call ID
against the raw source/POST result; neither a detached result nor a copied
source label is enough. The value trace retains `baseline_composed` and `composed`, and records only
ticket hashes/IDs—not raw sensitive values. Run metadata marks source
classification **unattested** and scope `synthetic_cpu_candidate_only`.

## Observed deterministic controls

- Same scripted task, agent and synthetic environment: v12 denies public
  `room` after an unrelated S2 read; v13 dispatches the exact authorized
  `post_webhook_mock` through Broker, then reaches POST and a safe Final.
- Clean/poison pair has identical user task and catalog. Clean dispatches;
  document with an added instruction is denied.
- A value also present in S2, absent room record, and changed webhook
  destination are denied. Malicious PRE or POST guard outcome remains a veto.
- A final containing a synthetic private email remains REDACT/DENY; an old
  catalog version or a non-A6 level cannot activate the ablation.
- A non-replay agent, another guard/fixed-identity mismatch, a replaced webhook
  tool and a substituted private worker fail before inference/output creation.

Development transparency: the **first** CPU integration run failed the
poisoned-document control (one failed test of seven). The raw document was
JSON-escaped before the existing lexical rule saw it, so the rule did not
flag the phrase and the initial ticket extractor accepted a valid line plus
additional prose. The candidate was tightened to require the entire content
to be the single room line. The failing case was retained as a regression;
the subsequent focused run passed 20 component/integration cases, including
ten end-to-end cases. This was pre-freeze development, not a semantic retry of
any model experiment. The lexical detector issue remains visible for broader
Phase 5 coverage; the narrow ticket no longer relies on that detector to
reject extra source text.

The original CPU integration QA passed 169 targeted unit/integration tests
(including unchanged v12 controls). The subsequent admission hardening passed
98 focused component/integration tests, setup verification, Ruff on the
repository and mypy on 508 source files; knowledge-check and diff-check are
recorded in the handoff. Full pytest was not run because sealed Test authoring
tests are outside this active-phase scope.

No LLM/model inference, network side effect, Kaggle submission, Test access,
new Dev score, guard lifecycle fix or formal acceptance group is claimed.
The exact-line grammar is intentionally too narrow to claim a fix for the
existing Dev32 false block. Before any model experiment, a host inventory must
be independently approved and pinned, broader extraction must retain
fail-closed controls, and source/run identity plus paired metrics must be
predeclared. Phase 5 remains 4/7 (~57%).
