# Phase5 Dev32 v2 — corrected native route and offline package

2026-09-23. V1 failed before its first worker started; the
[authenticated incident](phase5_clause_dev_gpu_v1_failure_report.md) identified
a duplicate `constrained` argument. V2 removes the caller argument on the native
route. The native guard factory still supplies the separately audited evidence
root. The fixed public Dev schedule, model/settings, tools and prior results are
unchanged.

[V2 contract](../architecture/phase5_clause_dev_package_v2_contract.md),
[development package](../../experiments/manifests/phase5_clause_dev_package_v2_dev01.json),
[credential scan](../../experiments/manifests/phase5_clause_dev_package_v2_scan01.json).

The bounded route test reproduces the v1 TypeError before the correction and
checks v2's admitted guard root through the actual runtime composition without
loading weights. The v2 launcher rejects working-tree native dispatch. Package
v2 development rehearsal passed both isolated archive/expanded mounts; each
ran 8 tools, 21 clean Dummy, 32 fixed Dev tasks, 8 shard audits and
missing-only/complete resume. The package has 213 worker files/222 source pins;
each layout has 1,027 raw hashes. Scan of 2,282 files found zero known
credential values.

Raw: `build/kaggle/phase5_clause_dev_package_v2_dev02`; selected receipt/scan:
`results/phase5_clause_dev_package_v2_selected01`. First development attempt
stopped before building on a missing v2 package-check script, then the separate
v2 script was added. No GPU was used during these checks.

QA01 passed 980 focused tests and 395 integration tests but was rejected for one
unused import in a test file. [QA02](../../experiments/manifests/phase5_clause_dev_package_v2_qa02.json)
passed 980 focused tests, 395 integration tests, Ruff, mypy on 501 source
files, setup and knowledge checks. It also confirmed 10 prior QA source pins,
182 frozen native source pins, and 169 tracked data hashes unchanged. No
Test/private GT payload was parsed. V1 failure evidence and source remain
immutable. A v2 source freeze/committed package and remote admission are still
required before any new native run. Completion/CPU tests do not establish model
quality or Phase5 acceptance; formal progress stays 4/7 (~57%).

The [first committed rehearsal](../../experiments/manifests/phase5_clause_dev_package_v2_release01_rejected.json)
at `build/kaggle/phase5_clause_dev_package_v2_release01` passed both mount
layouts, but its host release auditor still allowed the v1 launcher cache name.
The actual v2 rehearsal cache is `clause_dev32_kernel_v2.cpython-311.pyc`.
This is a package-admission defect, not a model run; release01 is **rejected**
and was never submitted. The v2-only auditor correction now derives the cache
path from the selected launcher and is covered by a regression test.
[Selected QA03](../../experiments/manifests/phase5_clause_dev_package_v2_qa03.json)
passed 981 focused tests, 395 integration tests, Ruff, mypy on 501 source
files, setup and knowledge checks; 7 unaffected QA02 source pins, 182 frozen
native source pins and 169 tracked data hashes remain unchanged. A new
committed release is required; the earlier QA02 remains immutable evidence for
the pre-correction source.

Release02 was built from GitHub main commit
`ad152ff8c8970df28cd6b5b0a0eebd02481b8e1e` and passed independent
[package authentication](../../experiments/manifests/phase5_clause_dev_package_v2_release02.json):
222 committed source pins, 213 worker files and both archive/expanded layouts,
each with 21 Dummy and 32 fixed Dev tasks. The release01 bundle remains
rejected and was not uploaded.

One private/offline/T4 Kaggle submission was accepted as the actual
[Dev32 v2 notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2),
version 1/ID 135499833, using the unchanged private
[guard Dataset](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
version 1 and Qwen2.5-7B model mount. The remote source, metadata, version and
source commit matched the [submission receipt](../../experiments/manifests/phase5_clause_dev_v2_gpu_submission01.json).
At 2026-09-23 09:55:43 UTC a read-only check reported RUNNING. No terminal
output or native quality score exists yet; do not resubmit or reuse v1 partial
output. Next: wait for terminal status, download to a fresh directory, record
before/after remote identity and independently audit the immutable raw files.

Terminal update: the notebook subsequently finished COMPLETE. The fresh
download, two byte-identical release audits, 32/32 task coverage and the
host-only descriptive results are documented in the
[v2 terminal report](phase5_clause_dev_gpu_v2_terminal_report.md). This
supersedes the RUNNING observation above but does not constitute guard-quality
or Phase 5 acceptance.
