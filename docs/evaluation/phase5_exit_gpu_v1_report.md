# ExitPair GPU v1 — terminal audit, 2026-09-21

Bounded Phase 5 diagnostic, not a lifecycle fix or population-quality estimate.
Phase 5 remains 4/7 acceptance groups (approximately57%); held-out Test stays sealed.

## Identity and verification

[Notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-exit-milestones-v1)
v1/ID135130970, source `6d039e255a0a0a91f6e514cfebe889c4b7ae8aed`.
Private/offline T4, timeout3600s; unchanged Qwen2.5-7B revision1, guard1.5B
[Dataset](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1 and image pins. [Submission](../../experiments/manifests/phase5_exit_gpu_submission01.json),
[release package](../../experiments/manifests/phase5_exit_pair_package01.json).

COMPLETE before download at 07:26:30 UTC and after download at 07:28:29 UTC on
2026-09-21. Notebook version, ID, private visibility and source remained identical.
[Terminal receipt](../../experiments/manifests/phase5_exit_gpu_terminal01.json).
The recorded interpreter is CPython3.12.13/Linux/x86_64; audit on the local Mac
binds that recorded runtime identity rather than incorrectly requiring host parity.

Two independently generated release audits are byte-identical. They validate
182 local/Git source pins, 176 archived worker files, 242 raw files and two remote
files, then re-audit native policy/token/attention/constraint/role/PID bindings.
[Audit receipt](../../experiments/manifests/phase5_exit_gpu_audit01.json).
Known credential-value scan:253 files, zero matches. Downloaded Python is not
executed. Raw is immutable in `results/phase5_exit_gpu_monitor01`; no backup to
another private storage destination has been configured.

## Results

The [summary](../../experiments/manifests/phase5_exit_gpu_summary01.json) is generated
by `scripts/report_phase5_exit_gpu_v1.py` after a fresh release audit; it is not a
manually edited score. Full audits are `results/phase5_exit_gpu_audit01.json` and
`results/phase5_exit_gpu_report01/release_audit.json`.

| Task | Terminal | Guard valid | Tool calls | Startup(s) | Task total(s) | Shutdown |
|---|---|---:|---:|---:|---:|---|
| CALC_A2 | completed | 2/2 | 1 | 271.917 | 281.885 | 2 GRACEFUL |
| CALC_A6 | completed | 2/2 | 1 | 166.523 | 175.187 | 2 GRACEFUL |
| DOC_A2 | completed | 2/2 | 1 | 166.240 | 176.093 | 2 GRACEFUL |
| DOC_A6 | completed | 2/2 | 1 | 166.236 | 175.956 | 2 GRACEFUL |

All eight constrained guard requests completed; no incomplete constraints,
invalid-output events or guard backend failures. All eight workers were reaped,
all four tasks recovered VRAM. Every role-bound target, finalizer and thread
shutdown stage returned. **No TERMINATE or KILL occurred in this run.**

Joined agent generation:8 calls,142 output tokens/18.643s =7.617tokens/s.
Joined guard generation:8 calls,134 output tokens/6.656s =20.133tokens/s.
Summed task startup:770.916s; summed task total:809.121s (about13.49min).
These are descriptive measured denominators: generation excludes startup;
task total excludes notebook bootstrap/download and runner recovery sampling.
The time between status observations is not notebook runtime. No statistical
speedup or hardware-normalized comparison is claimed.

## Interpretation and next step

The previous constrained diagnostic recorded4TERMINATE/4GRACEFUL. This run's
8GRACEFUL is a positive observation, **not evidence that instrumentation fixed
the intermittent teardown failure**. It did not reproduce the symptom, and
Python observation itself may affect timing. There is no controlled paired
experiment isolating that effect, nor an identified native destructor/thread cause.
Do not erase old failures, raise grace2s or retry successful tasks until favorable.

The diagnostic schedule covers calculator/document actions only. Eight syntactically
valid responses do not establish guard classification quality, benign external-sink
utility, SQL authorization, final-sink protection or the whole20DoD mapping.
Keep lifecycle reliability open. Next prepare a public-Dev coverage matrix for
DoD5/9/13/14/15/16 from declared tasks and policy expectations, without selecting
on model success or consulting held-out Test. A later lifecycle comparison needs
a prospective fixed repeat/order budget and separate run identity, not a rerun
of this accepted diagnostic for a better score.

## Final verification

The summary adapter has10new tests, including mismatched PID/method, invalid
join/role coverage, immutable inputs and delegated validation failure.
[Scoped QA](../../experiments/manifests/phase5_exit_gpu_qa01.json):773 focused
unit/regression tests passed in50.12s;180 integration tests passed in186.44s.
Setup, Ruff, mypy468, knowledge links and diff checks passed. All prior frozen
source/QA pins remain intact. Full repository pytest was not run because sealed
Test-authoring fixtures remain excluded; no Test/private oracle payload accessed.
The selected QA distinguishes the current host Git base from the older CPU
control base inherited by the raw collector; its raw receipt hash is retained.

No new inference, job submission, commit or push in this terminal-audit work.
Worker source stays frozen; host summarizer/tests and selected evidence remain
local for a later meaningful closeout.
