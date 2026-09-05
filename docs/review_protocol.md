# Phase 2 Review Protocol

The project owner explicitly waived review because Huy and Minh work on the
same machine. Records must not name a fabricated reviewer or claim that the
owner inspected each task.

Every task instead requires all ten deterministic/owner checks: clarity,
solvability, ground truth, tool path, arguments, alternative paths, distractors,
category, leakage, and synthetic privacy. The only accepted mode is
`automated_checks_owner_waiver`; `accepted_by` is `automated_gate`. Rejected or
repaired records are retained in the
changelog/report when they occur.

This provides reproducible QA but is not independent human review. The final
data card must disclose that limitation.
