# Observer native v2 — running diagnostic

2026-09-15. [Notebook v1](https://www.kaggle.com/code/huylmhuhu/react-vn-observer-native-v2),
ID134481763; observed RUNNING at11:19:36UTC, no failure message.
[Submission](../../experiments/manifests/phase5_observer_native_v2_submission01.json),
[remote source/version verification](../../experiments/manifests/phase5_observer_native_v2_monitor01.json).
Notebook and Dataset are private; team members need the owner's Kaggle access.

Source `c0930bfafc1a8bf0e894f5be8e52772cb4f511a5`, GitHub evidence `cf871a3`
pushed before submission. Fixed [Dataset](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1, agent `qwen-lm/qwen2.5/transformers/7b-instruct/1`, guard1.5B content snapshot
inside the Dataset. Private/offline two-T4 image, timeout14400seconds.
Before admission:23.08hGPU remaining; Datasetready/v1. Remote executable matches
the source hash in preflight and live version is1.

The schedule is four independent CALC/DOC × A2/A6 tasks. The new observer stores
bounded syntax hints and an independently computed host response hash. Preserve
every native terminal outcome and any zero-tool/zero-guard coverage. It is a
separate diagnostic, not replacement of the112-task Dev baseline.

Preparation: [53focused QA and historical load/policy helper re-audit](../../experiments/manifests/phase5_observer_native_v2_qa01.json);
[preflight03](../../experiments/manifests/phase5_observer_package_v2_cpu03.json),
153packagefiles/159sourcepins/706raw reverified,66.21seconds. Both layouts run
8tools,21cleanDummy, valid/malformed observer and completed/missing resume.
Synthetic boundary tests are not proof of native model execution.

Raw operational paths:

- `results/phase5_observer_native_v2_access01`
- `results/phase5_observer_native_v2_submission01`
- `results/phase5_observer_native_v2_monitor01/remote`
- `results/phase5_observer_native_v2_status02`
- `build/kaggle/phase5_observer_package_v2_preflight03/kernel`

When terminal: observe exact version/status again, download into a fresh path,
and retain any failure. If COMPLETE, run `scripts/audit_phase5_observer_gpu_v2.py`
with raw/remote/preflight/submission and a terminal observation binding the
submission hash, actual version/id and remote file hashes. It validates source/
bootstrap and independently repeats native audit without executing downloaded
code. Keep both audit outputs repeatable, scan credentials, summarize timing,
guard format categories, tool coverage and cleanup. Update this report and the
Kaggle directory with the terminal receipt. No new submission while v1 exists.
