# Ordinary repeated-request native entry v1

Phase 5 technical plumbing only, not A0–A6 adoption or model quality acceptance.
Preserve prior measured sources, policy/attention wrappers and supervisor.
New files: `llm/ordinary_pair_probe_v1.py`, `scripts/run_phase5_ordinary_pair.py`
and their CPU tests. No Test payload/private evaluator data or model inference
is needed for local acceptance; Kaggle remains the future inference worker.

## Inputs and ownership

Freeze public synthetic A and B fixtures in `inputs()`: A reuses the existing
small-context technical inputs; B repeats the public library-hours notice 32
times, with the existing guard prompt/schema. These are not benchmark tasks,
attack controls, tuned model prompts or an exact 4096-token boundary. Actual
tokenized geometry must be read from native metrics in a later run.

Order: agent A, guard A, agent B, guard B, agent A, guard A. One fresh sibling
pair per rehearsal, one resident worker per role. Each request gets fresh
message dictionaries and GenerationConfig: greedy temperature 0, seed 42,
caps 512 agent/128 guard. No forced minimum, extra forward or semantic retry.
Repeated A equality is descriptive, never a success filter. No tool actions,
benchmark state or hidden reasoning are retained; response text is hash-only.

The native builder composes original AgentFactoryV2/GuardFactory directly via
policy_pair: Ready → thread progress → policy → attention → native. It checks
the exact content-bound guard snapshot and fixed role identities before
transport allocation. Three fresh, disjoint, non-symlink roots must not overlap
model inputs. No private factory mutation and no native loading in the host.
The native PairConfig/deadlines/caps remain unchanged. Both roles start, so this
entry is not suitable for agent-only A0/A1 runtime ownership.

## Durable observations and acceptance

The manifest binds asserted source commit, pair config, inputs and generation
hashes, role revisions, seed, order and recovery parameters before startup.
Submitted and returned receipts are separate: a response followed by an
observer failure is still counted as returned. Host call duration excludes the
after-call memory observation; this is not uninstrumented model latency.
Native metrics/policy/attention live in their own roots and are not rewritten.

Observe baseline, combined residency, each return and six post-close samples.
Use unchanged two-device MIN_RESIDENT and 256 MiB recovery tolerance. Persist
supervisor snapshots and error classes only; propagate interrupts after cleanup.
No retry/resume, fallback backend, truncation or overwriting a previous output.
Reaping, graceful exits, memory recovery and IPC cleanup remain distinct claims.

`execution_valid` covers completion plus observed cleanup/recovery only;
`native_validated` and `phase5_accepted` always remain false here. Native call
count remains unknown until independent artifact audit, rather than inferred
from six returned strings. Source commit supplied by environment is an asserted
identity, not source authentication. Summary files are not an independent audit.

CLI defaults to stub: real spawned transport but fake model responses and GPU
memory, without native policy/attention execution. Its native branch requires
explicit `--backend hf` and all model/evidence paths. Validate paths/snapshot
before any Torch/CUDA initialization; version and two-T4 checks remain in HF
mode only. CPU tests cover real spawn, lazy native wiring, immutable A/B/A,
failure/interrupt cleanup, count preservation, no retry and early refusal.

Before a GPU submission: independent supervisor-bound native policy/attention/
metric audit; publisher/tokenizer/source/load/memory authentication; exact
package/import/layout preflight; then current quota/private Dataset check.
This entry alone does not authorize declaring these gates passed. A0/A1 owner,
runtime differential/lifecycle, A4/general final and grouped Dev work remain.
