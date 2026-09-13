# Phase 5 corrective runtime v7 / components v2

Status: implementation under CPU validation; not Phase 5 acceptance or a
production guard freeze. Supersedes v1 entitlement/v6 for new development.
Historical source, receipts and raw artifacts remain unchanged for audit.

## Authorization and final sink

- `final_entitlement_v2` represents individual `(source_type, source_id,
  value_type)` grants. Each affirmative clause must contain exactly one source;
  ambiguous multi-source and incomplete clauses grant nothing. Quoted raw input
  grants nothing, including multiline quotations. Several types for one source
  are permitted. Table names are a distinct namespace from DOC/CACHE IDs.
- Supplied host objects must exactly equal canonical extraction of the raw
  instruction, including profile/explicit/grants/hash. The runtime validates
  before output/guard creation and derives independently within each task.
  Hash equality alone is not a grant. Oversized raw input is rejected before
  execution; this is not a model terminal/quality result.
- Final screening masks every exact protected span, including entitled spans,
  then scans the residual for transformed duplicates. Normalized-only/residual
  evidence or incomplete source coverage denies to an empty final. Unauthorized
  raw spans redact. Source labels and proposal ancestry remain conservative.
- `typed_value_origin_v2` recognizes synthetic `SV_SYN_<3..12 digits>` IDs in
  typed DB/document fields and text, preserving exact source pointers. Unsupported
  non-null values in recognized typed fields invalidate coverage rather than
  silently disappearing. The v1 record/byte/depth budgets still apply.

## Cumulative runtime scope

- A0–A3 retain their existing behavior; processing scope is enabled only for
  A4–A6. A0–A5 metadata has no A6 final policy. The bounded v2 scope retains
  exact document/page anchors and pairs each table with its granted/observed
  columns, avoiding cross-table authorization.
- Scope is composed with existing PRE decisions before the Broker. A scope
  denial cannot be discharged as unrelated sensitivity by A6. Source observations
  occur only after actual Broker execution and host source validation. Missing
  or inconsistent document/page source catalog mappings deny before execution.
- The runtime reuses the frozen v5 task loop with run-local policy classes and
  function dependencies. No process-global mutation or second ReAct loop.
  The session-policy MRO remains visible to session/guard auditing. Scope state
  and traces are task-local and do not enter model prompts.
- External sinks and calculator delegate to existing policies. No tool schema,
  agent prompt, decoding or mock network behavior changes. This does not add
  a new final LLM classifier or claim general semantic intent detection.

## Evidence protocol

`scripts/verify_phase5_remediation.py` reserves a fresh result directory,
records source/dependency/synthetic input identities, runs focused regression
and full development QA, and stores logs, JUnit and focused runtime traces.
Tracked data is hashed without parsing held-out payloads. Historical receipt
audits compare actual source/raw bytes, not `valid` flags. A new receipt is
re-audited before export; prior corrupt receipts are explicitly separate.
Dirty worktree QA is labeled as such and is not called a clean release.

The repair scope is synthetic regression/parity, not benchmark ASR, accuracy,
utility or GPU throughput. Required further work: production ModelPair runtime
and graceful GPU lifecycle, guard quality on grouped Dev, broader origin/scope
coverage and a formal Phase 5 freeze. No Phase 6/7 work or held-out tuning.
