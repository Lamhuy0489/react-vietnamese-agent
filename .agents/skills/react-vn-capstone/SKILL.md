---
name: react-vn-capstone
description: Implement, review, or close a phase of the Vietnamese ReAct tool-agent capstone while preserving scope, phase boundaries, research validity, and repository acceptance criteria.
---

# Vietnamese ReAct Capstone

Use this skill for project implementation, phase planning, phase review, or
handoff work in this repository. Do not activate it for unrelated generic
Python work.

1. Read `../../../docs/project/phase_status.md`,
   `../../../docs/project/research_contract.md`, and
   `../../../docs/project/invariants.md`.
2. Identify the active phase in `../../../docs/project/phase_map.md`, then read
   that phase's detailed file under `../../../plan/` only as needed.
3. State inputs, allowed files, acceptance criteria, and whether held-out data
   could be touched before implementation.
4. Freeze shared interfaces before parallel work. Implement only the smallest
   coherent change within the current phase.
5. Add deterministic tests or validators and run the relevant checks.
6. Report changed files, artifacts, checks, remaining issues, and any access to
   held-out data.
7. Update phase status only when every required acceptance criterion passes.

Never cross into a later phase for convenience. Do not change frozen research
scope silently; add a decision-log entry and explain the impact. GitHub is the
source of truth and Kaggle is only an inference worker.
