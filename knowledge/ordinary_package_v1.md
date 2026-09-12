# Exact ordinary A/B/A Kaggle package

Source wrapper/builder commit `c9749fa`; [package contract](../docs/architecture/phase5_ordinary_package_v1_contract.md).
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
Kernel version 1 đã được submit nhưng dừng ở accelerator gate trước native model:
Kaggle trả `machine_shape=Gpu` và runtime chỉ thấy 1 GPU, trong khi contract
cần 2 T4 (`RuntimeError: two T4 devices required`). Source kéo về vẫn khớp
wrapper hash; bootstrap, 21 Dummy, tokenizer sidecars và log được tải riêng tại
[remote error receipt](../experiments/manifests/phase5_ordinary_pair_gpu_v1_error01.json).
Không có model generation/tensor/quality output. Default CLI credential là `lamhuy8904`
and cannot read this private Dataset (403), so future commands must explicitly
use the owner credential without printing it.

Đã xác định nguyên nhân là lệnh push truyền accelerator alias `gpu`, làm metadata
remote thành generic `Gpu`; không retry cùng identity. Lượt sửa phải dùng kernel
identity mới và accelerator enum `NvidiaTeslaT4`, rồi kiểm device count trước
model initialization.

This is package/preflight evidence only: native A/B/A, current remote source
authentication, quality, A0–A6 runtime gates and Phase 5 acceptance remain open.
