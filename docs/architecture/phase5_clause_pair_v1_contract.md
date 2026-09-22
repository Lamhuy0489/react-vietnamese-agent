# Phase5 — clause runtime / constrained ExitPair integration v1

2026-09-22. This is a separate host runtime, not a replacement of historical
workers and not authorization to reuse a previous notebook identity.

## Inputs and boundaries

- Compose validated runtime v12, raw-clause anchors v3, host-origin v3 and
  host-bound resource/SQL scope v5 with the frozen constrained classifier,
  prompt, cache/decoding identity, native factories and ExitPair observation.
- Only task-local function bindings change. Imported module globals, model
  identities, native decoding limits, worker lifetimes and two-second graceful
  cleanup budgets remain unchanged. A0/A1 are not routed through this paired
  guard adapter; v12's A0 delegation remains separate.
- Scope v5 requires explicit host resource and row bindings both in the outer
  pre-start admission check and inside the task. Supplying only the old
  one-argument constructor is invalid and must be caught before GPU packaging.
- Inputs are raw public tasks and host source catalogs. No Test payloads, private
  GT, coverage expectations or project memory enter policy or model prompts.

## Version and read-only audit contract

Runtime identity: `security_runtime_v12_constrained_exit_v1`. Retain original
pair receipts, guard witnesses, constraint receipts and child exit milestones.
Add the three candidate profile identities and raw authorization metadata.
Record the source/config/task identities separately from Git base: a working-tree
hash is not a committed GitHub release.

The candidate auditor joins existing transport/cache/constraint/lifecycle checks,
then recomputes raw-user authority and replays A6 origin admission from serialized
source artifacts and value traces. It compares every origin record/label/hash and
the saved index identity. These checks detect record corruption, not arbitrary
semantic correctness of all guard/value decisions. Behavioral controls remain
required. Audit must not invoke model generation or change raw files.

Checkpoint validation uses recorded interpreter identity when auditing another
host. It rejects old runtime identities, modified source pins or raw receipts;
only missing tasks can run during an exact-identity resume. Existing completed
and model_error results are retained, never retried for a better outcome.

## CPU controls and native gate

The four existing calculator/document paths at A2/A6 run under valid and
deliberate backend-failure conditions. Four additional synthetic paired controls
read a private and a public document, then attempt email: public A6 allowed;
sensitive A6, unknown A6 and public A5 denied. These scripted controls use four
steps (two reads, one send, one final); the historical diagnostic/native budgets
are not increased. All sinks stay mock-only.

Acceptance here requires exact outcomes, preserved failures, two read-only audits,
reaped workers, immutable resume, and negative metadata/source corruption tests.
These are CPU integration controls, not native model or quality measurements.
No new four-task GPU diagnostic is required merely to repeat old lifecycle data.
Next prepare the predeclared 32-task paired Dev workload, bind native receipt and
checkpoint identities, rehearse archive/expanded packages, and only then freeze
source and submit. The worker cannot be claimed v12 by changing metadata alone.
