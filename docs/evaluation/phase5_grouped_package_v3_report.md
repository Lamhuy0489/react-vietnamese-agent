# Grouped Dev package v3 — independent worker rehearsal

2026-09-14; source `0d865365b7881144756f804441ca24ed48935f7f`.
Packaging repair only; native runner/auditor v2 and public Dev selection unchanged.

## Verified

- Complete source archive: 170 files; 175 source/build/contract hashes bound to Git.
- Both archive and generated-expanded mounts executed in fresh offline venvs,
  with no editable install. Each recorded 128 module origins inside packaged src.
- Each layout: eight tool schemas and recovery; 21 clean Dummy tasks, completed
  resume and missing-only resume; 112 grouped stub keys across eight shards.
- Grouped first-task checkpoints survive resume unchanged; completed shard resume
  is immutable. These are transport/runtime tests, not LLM utility or ASR/FPR.
- 2,083 raw files per layout; 4,357 source/raw/kernel hashes independently rechecked.
- 14 new regression tests passed (0.82s), including wrong-root fallback, foreign
  namespace, unsafe tar members, exact root/hash checks and no-retry native routing.

[Frozen preflight receipt](../../experiments/manifests/phase5_grouped_package_v3_preflight01.json)
SHA-256 `d929631e5557e656e21b1394b39a4175aec310883367d2a1ac3fedd8cbe1ec52`.
Local immutable raw root: `build/kaggle/phase5_grouped_package_v3_preflight01`.
No weights loaded locally, no inference on Test/private ground truth.

The old compile/import receipts remain unchanged but are **not** accepted as
isolation evidence; see [withdrawal/cause](phase5_grouped_native_v2_report.md).
Full repository QA is separate; this preflight receipt deliberately does not
itself authorize native submission or mark Phase 5 accepted.

## Full repository QA

**3,113 passed / 1 optional native-tqdm skip / 1,060.05s**. Setup, Ruff,
mypy (392 files) and knowledge checks pass. 555 source, seven raw report/log/XML
files and 169 frozen-data hashes independently checked. The separate fresh-venv
package rehearsal installed pinned tqdm; the development environment did not.
[Selected CPU QA receipt](../../experiments/manifests/phase5_grouped_package_v3_cpu01.json).

Scope correction: the QA runner's broad `test_payload_accessed=false` field is
not an access audit of the whole historical unit/authoring suite, which includes
Test-assigned fixtures. The selected receipt explicitly marks that field unknown
and preserves the original report/hash unchanged. No held-out LLM experiment or
tuning occurred; the **new worker package** includes only public Dev payloads.

## Live prerequisites and next step

Selected owner `huylmhuhu`: GPU quota 29.02/30h remaining; private guard Dataset
ready/version 1; Qwen model instance version 1 accessible. These are dated live
checks ([live receipt](../../experiments/manifests/phase5_grouped_package_v3_live01.json)),
not a quota reservation. An initial local model-metadata destination
error was corrected without downloading weights or changing remote state.

Full QA passed and source/evidence pushed as `93dc9a2`. One private/offline T4x2
shard (14 keys) has been submitted as
[react-vn-grouped-dev-v3-shard-0](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-0)
v1, currently RUNNING. [Submission receipt](../../experiments/manifests/phase5_grouped_v3_s0_submission01.json).
Remote wrapper SHA-256 matches the frozen package; private/offline/image/model/
Dataset metadata verified. Requested `...-s0` became `...-shard-0` due to title.

14,400s timeout, as frozen in the [contract](../architecture/phase5_grouped_package_v3_contract.md).
Record the returned notebook URL/version, not an assumed slug. Preserve native
failures; independently authenticate downloaded source and audit artifacts before
spending quota on the remaining seven shards. Phase 5 remains 4/7≈57% accepted gates.
