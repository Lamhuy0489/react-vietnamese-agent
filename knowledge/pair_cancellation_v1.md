# Pair cancellation v1 — GPU resource audit, 2026-09-09

## Hiện hành: real GPU technical scope pass

Kernel `huylmhuhu/react-vn-pair-cancel-v1` version1 COMPLETE lần submit đầu;
sourcee01b4e7/receipt push mainf6474a7 trước GPU. Exact Docker digest/private/
offline/twoT4/Datasetv1/model pins match. [Report](../docs/evaluation/phase5_pair_cancel_gpu_v1_report.md),
[selected audit](../experiments/manifests/phase5_pair_cancel_gpu_v1_audit01.json).

Ba fresh pairs: agent_busy180,383s/guard_busy120,337s/ignore_term120,823s.
Six workers reaped,5TERMINATE/-15+1KILL/-9, không graceful. Mỗi ca residentdelta
9,799/7,621GiB và six recoverysamples residual0bytes haiGPU (18samples tổng).
Six model loads, zero model.generate; tinyCUDA busy loop không nativegeneration.
Raw91files,21Dummy/84events/hash/identities audited; hai JSON/report byte-identical.
24new audit tests pass; final full suite1.430tests/353,52s pass;
setup/Ruff/mypy236files/knowledge pass. Không test/kernel/model job còn chạy.
[Release QA](../experiments/manifests/phase5_pair_cancel_gpu_v1_release_qa01.json).

Resource-tracker warning3leaked semaphores khi interpreter shutdown được lưu
nguyên trạng. Không đủ dữ liệu để chỉ nguồn tạo hoặc bảo đảm persistent leak
sau tracker cleanup; IPC cleanup unverified, không claim mọi resource sạch.
Tiếp theo bounded diagnostic riêng, không unregister semaphore hoặc nới grace
để giấu warning. Context stress/runtime/Dev/model decision/A4/final còn mở.
Không retry/localweights/Test payload/Phase5 acceptance.

## Lịch sử GPU packaging trước submit

Đã có lazy HF factories/entry script và standalone wrapper13file;17new tests
pass. Giữ11pair overlay và CPU cancellation module hash, pinned Docker image
đã thấy ở run cũ. [GPU contract](../docs/architecture/phase5_pair_cancel_gpu_v1_contract.md).
Sourcee01b4e7 exact preflight pass cả archive/expanded/PAX,8tools/21Dummy/resume/
three stub trials. Full QA1.406tests/369,92s, setup/Ruff/mypy234files/knowledge pass.
[Receipt](../experiments/manifests/phase5_pair_cancel_gpu_v1_preflight01.json),
[QA](../experiments/manifests/phase5_pair_cancel_gpu_v1_pre_submit_qa01.json).
Pre-submit quota29,22h; Dataset11942593 private/v1/READY. Source/receipt push
trước private GPU submit1 `huylmhuhu/react-vn-pair-cancel-v1`, timeout5400s.

## Mốc CPU đã hoàn tất

[Contract](../docs/architecture/phase5_pair_cancellation_v1_contract.md).
Ba fresh pairs theo thứ tự agent_busy,guard_busy,guard_ignore_term. Wrapper
giữ backend resident, không gọi model.generate; host busy command chạy smallCUDA
chỉ khi explicit HF mode. CPU dùng backend/memory giả lập và real spawn.

Durable baseline/ready/busy/closed/recovery/trial/summary; stop-after-failure,
giữ error class, cleanup cả hai, không pass khi handle pending hoặc thiếu reap.
Timeout agent180/guard120 trong contract GPU, CPU rehearsal0,2s ghi riêng config.
Ca thường TERMINATE/-15, ignore-term KILL/-9; sibling method ghi đúng thực tế.
Không thay nguồn ModelPair/WarmGuard/HF v1/v2 hoặc kết quả pair GPU62files.

Source5d326bf đã chạy hai clean-source rehearsals validation01/02; cả ba ca đều
pass,12workers reaped, stable summaries identical.44raw files/run +receipt,
raw PID/timing bytes khác nhau.18synthetic recovery samples/run match baseline.
[Selected receipt](../experiments/manifests/phase5_pair_cancellation_v1_validation01.json),
[report](../docs/evaluation/phase5_pair_cancellation_v1_report.md).
Full final-source QA1.389tests/356,32s pass,26new tests gồm cleanup-interrupt.
Setup/Ruff/mypy231files/knowledge pass; không test/kernel job còn chạy.
[Release QA](../experiments/manifests/phase5_pair_cancellation_v1_release_qa01.json).
CLI `scripts/probe_phase5_pair_cancellation.py`
chỉ CPU;146prior entries và11GPUoverlay,62GPUraw hashes giữ nguyên; Test hash-only.

Ở mốc CPU, bước tiếp là exact GPU packaging; bước này và combined busy-VRAM
evidence đã hoàn tất ở phần hiện hành phía trên.
Context stress cần protocol riêng: exact tokenized input và forced-length nếu
muốn chứng minh4096+512, không suy ra từ early EOS. Không chọn guard/quality,
runtime integration hoặc Phase5 closure. Không pending account/model access mới.
