# Phase 5 Dev32 v2 — terminal artifact audit and descriptive results

2026-09-23. The private/offline/T4 [Kaggle notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2)
finished COMPLETE at version 1/ID 135499833. It used frozen GitHub worker source
`ad152ff8c8970df28cd6b5b0a0eebd02481b8e1e`, the private
[guard Dataset](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
version 1 and the same Qwen2.5-7B mount/settings as the predeclared release.
The remote code, metadata, version and source SHA matched the submission both
before and after downloading. No new inference or retry was performed.

[Selected terminal receipt](../../experiments/manifests/phase5_clause_dev_v2_gpu_terminal01.json),
[release02](../../experiments/manifests/phase5_clause_dev_package_v2_release02.json),
[submission](../../experiments/manifests/phase5_clause_dev_v2_gpu_submission01.json).
Raw/remote outputs are under `results/phase5_clause_dev_v2_gpu_monitor01`.
Two independent runs of `scripts/audit_phase5_clause_dev_gpu_v2.py` were
byte-identical (SHA-256 `8d0f962eac91934003ebde2264b8aba2e3a94a2cd48342b2c904c3e979349324`):
222 committed source pins, 2,073 raw files, two remote files and all eight
shards/32 fixed public Dev task IDs verified. The 16 attack and 16 matched
benign cases each cover A2 and A6; all 32 have terminal `completed` checkpoints.
No Test payload or private ground truth was accessed. A known credential-value
scan over 2,077 raw/remote/report files found zero matches.

The reproducible host-only [descriptive summary](../../scripts/report_phase5_clause_dev_gpu_v2.py)
was generated twice from the two identical audits; both summary JSON and task
CSV hashes match. It reports observable behavior, not oracle scores:

| Observation | Result |
|---|---:|
| Agent/guard generation calls | 69 / 65 |
| Returned guard classifications | 65/65 `OK` (37 PRE, 28 POST) |
| Tasks with no guard invocation | 8/32; not guard-quality successes |
| Tool proposals/results | 28/28; 24 `ok`, four tool errors |
| Security-trace `denied` events | 9 (five attack, four benign at A6) |
| Worker exits | 32 agent GRACEFUL; 31 guard GRACEFUL, one guard TERMINATE |
| Task wall time, median / p95 nearest-rank / max | 197.49 / 204.33 / 301.40 s |
| Task startup median | 180.09 s |

The summed per-task wall time is 6,407.11 s, including 5,872.12 s of startup;
it is not a measured end-to-end calendar duration. The four tool errors are
two `INVALID_QUERY` and two `NOT_FOUND` results, retained in the raw trace.
All eight no-guard tasks were final-answer paths without a guard request;
`constrained_counts_verified=False` for those paths is not silently promoted
to a passing guard check. A guard worker needed TERMINATE on the first task;
this prevents a 100% graceful lifecycle claim. Remote model mount metadata
was authenticated, but a cryptographic hash of the model weight files was not.

Passing artifact integrity, returned JSON syntax and task completion does
**not** establish ASR, FPR, benign utility, attack prevention or final-answer
semantic safety. In particular, the nine DENY events and two final REDACT
decisions need Dev-oracle comparison before calling them correct or overblocking.
The selected run does not close DoD-5/15/20 or Phase 5 formal acceptance;
progress remains 4/7 (~57%) acceptance groups. The next distinct task is a
versioned, evaluator-only Dev scoring pass over these immutable traces with
predeclared denominators and error handling. Do not rerun this notebook for a
better semantic result and do not open held-out Test.
