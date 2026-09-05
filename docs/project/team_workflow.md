# Team Workflow

## Ownership

- Lâm Quang Huy: ReAct/control flow, policy, A1–A4, security evaluation/RQ2.
- Nguyễn Quang Minh: synthetic environment/data flow, normalization,
  provenance, A5–A6, capability/robustness evaluation/RQ1/RQ3.
- Shared: interfaces, integration, A6 end-to-end behavior, review, final runs,
  and thesis convergence.

Both members author 125 clean tasks and 35 canonical attack families, then
cross-review the other member's work.

## Git workflow

- Protect `main` after the initial scaffold.
- Use short-lived branches named `phase-N/<topic>`.
- Require one teammate review for benchmark/schema/security changes.
- Keep secrets and generated run artifacts outside ordinary commits.
- Tag frozen datasets/configurations/results; record any post-freeze deviation.

## Handoff template

Each task handoff reports changed files, contract decisions, checks run,
artifacts produced, unresolved issues, and whether held-out data was accessed.
