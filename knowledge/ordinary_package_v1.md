# Exact ordinary A/B/A Kaggle package

## Current native follow-up

The corrected new identity `huylmhuhu/react-vn-ordinary-pair-t4x2-v1` was
submitted with the explicit `NvidiaTeslaT4` accelerator and completed.  Its
remote source, metadata and 132-file raw output are independently authenticated
in [the T4×2 release audit](../experiments/manifests/phase5_ordinary_pair_t4x2_v1_audit01.json).
The package source and wrapper remain the same; the earlier generic-`Gpu`
identity below is retained as an immutable infrastructure error receipt.

The native run loaded both pinned models and returned six A/B/A ordinary calls;
the worker-produced joined audit equals two fresh local audits byte-for-byte.
This closes the package-to-native technical milestone only.  It does not close
quality, ASR, A0–A6 runtime integration, grouped Dev validation or Phase 5.

Package wrapper/builder was introduced at `c9749fa`; the exact selected source
commit used by preflight and the native kernel is
`a412e571a6fba89103b93c55eb830106bede2d01`.  See the [package contract](../docs/architecture/phase5_ordinary_package_v1_contract.md).
The offline preflight generated `build/kaggle/phase5_ordinary_pair_v1_preflight01`
with 56 source-overlay files and a new private kernel layout. Both archive and
expanded source mounts passed in an isolated Python environment.

Each layout ran the frozen eight-tool/recovery check, 21 selected public Dev
Dummy tasks, missing-only resume preserving 20 checkpoints, ordinary stub A/B/A
with six calls, two independent ordinary audits, metadata collection and two
joined synthetic audits. Worker PIDs were distinct per layout. No weights,
native model, tensor or Test payload entered local execution. The generated
kernel metadata uses new identity `huylmhuhu/react-vn-ordinary-pair-v1`, private
Dataset `huylmhuhu/react-vn-guard15-probe-data-v1` version 1 and Tesla T4.

The worker sequence is metadata collection → native ordinary pair → joined
tokenizer audit; any failure stops without semantic retry. The exact wrapper
reuses the pinned base bootstrap and source archive, sets the packaged `src` in
subprocess `PYTHONPATH`, and rejects stale selected Git bytes. It does not
include the source-envelope tokenizer fixture in the model payload.

Package unit tests: 16 focused tests pass (the combined package/tokenizer/runner
set is 82 pass). Full QA completed with 2,304 pass/1 optional skip in 454.22s;
JUnit and the concise [release QA receipt](../experiments/manifests/phase5_ordinary_package_cpu_v1_release_qa01.json)
bind the package hashes. Current Kaggle checks with credential `kaggle1` (owner
`huylmhuhu`) show GPU 29.93h remaining and Dataset status `ready`, version 1.
Lượt kernel đầu version 1 đã được submit nhưng dừng ở accelerator gate trước native model:
Kaggle trả `machine_shape=Gpu` và runtime chỉ thấy 1 GPU, trong khi contract
cần 2 T4 (`RuntimeError: two T4 devices required`). Source kéo về vẫn khớp
wrapper hash; bootstrap, 21 Dummy, tokenizer sidecars và log được tải riêng tại
[remote error receipt](../experiments/manifests/phase5_ordinary_pair_gpu_v1_error01.json).
Không có model generation/tensor/quality output ở lượt lỗi đầu. Default CLI credential là `lamhuy8904`
and cannot read this private Dataset (403), so future commands must explicitly
use the owner credential without printing it.

Đã xác định nguyên nhân là lệnh push truyền accelerator alias `gpu`, làm metadata
remote thành generic `Gpu`; không retry cùng identity. Lượt sửa phải dùng kernel
identity mới và accelerator enum `NvidiaTeslaT4`, rồi kiểm device count trước
model initialization.

The old paragraph describes only the first failed identity.  Native A/B/A and
current remote source authentication are now recorded in the T4×2 follow-up
above; quality, A0–A6 runtime gates and Phase 5 acceptance remain open.
