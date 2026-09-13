# Repository Guidance

## Start here

This repository implements the research plan in the root Word document and
`plan/`. Treat `docs/` as the concise operational contract and `plan/` as the
detailed rationale/checklists. Read `docs/project/phase_status.md` before work,
then load only the documents relevant to the active phase.

For continuity, next read `knowledge/current_status.md` and
`knowledge/handoff.md`. Use `knowledge/README.md` as the navigation index;
historical notes do not override current status or the research contract.
Before handing off meaningful work, update the active task, next concrete step,
verification evidence and pending access in `knowledge/handoff.md`. Never put
credentials, private ground truth or held-out payloads in project memory.
Run `make knowledge-check` after changing knowledge links or handoff structure.
This is development memory only: do not inject it into benchmark model prompts.

Keep `knowledge/kaggle_resources.md` as the team's notebook/Dataset directory.
After a Kaggle submission or terminal audit, record the actual notebook URL and
version, Dataset URL/version, source commit, dated status, and report/receipt
links. Preserve failed/historical identities; distinguish requested aliases
from actual handles. Record access caveats, never credentials. Do not claim
remote availability from local link checks or make private resources public.

## Source-of-truth order

1. Explicit user instruction for the current task.
2. `docs/project/research_contract.md` and `docs/project/invariants.md`.
3. The active phase file referenced by `docs/project/phase_map.md`.
4. The root Word plan for approved scope and team allocation.

Do not silently change research scope. Record contract changes in
`docs/project/decision_log.md` with rationale and impact.

## Non-negotiable invariants

- GitHub is the source of truth; Kaggle is an inference worker.
- Use only synthetic data. Never commit credentials, tokens, personal data, or
  raw secret-bearing environment files.
- `send_email_mock` and `post_webhook_mock` must never perform network I/O.
- Do not store or request hidden chain-of-thought. Log only observable actions,
  tool results, gate decisions, and final answers.
- Every tool call goes through the Tool Broker.
- A0 contains no security defense beyond schema validation and tool limits.
- Evaluator ground truth is unavailable to prompts, runtime policy, and models.
- Sensitivity and trust are independent dimensions.
- The final answer is a security sink and must be evaluated as such.
- Split attack data by canonical family; a family and its benign pair never
  cross Dev/Test.
- Never tune prompts, policy, architecture, or thresholds using held-out Test.

## Phase discipline

- Work only inside the active phase unless the user explicitly changes scope.
- Freeze public interfaces before parallel implementation.
- Update `docs/project/phase_status.md` only after acceptance checks pass.
- Prefer deterministic validators for dataset, split, hash, and run integrity.
- Do not claim a phase is complete from file presence alone.

## Python quality

- Target Python 3.11+ and keep public interfaces typed.
- Keep notebooks thin; core logic belongs under `src/react_agent/`.
- Add or update tests for behavior changes.
- Before completion run: `python scripts/verify_setup.py`, `ruff check .`,
  `mypy src scripts`, and `pytest` (or explain unavailable dependencies).
- Avoid unrestricted `eval`, broad exception swallowing, and implicit network
  side effects.

## Repository hygiene

- Preserve raw research inputs in the root and `plan/`.
- Generated logs/results remain untracked unless explicitly selected as frozen
  release artifacts.
- Never add files from `credential kaggle/` to Git.
- Use small, reviewable commits and do not mix formatting-only changes with
  behavioral changes.
