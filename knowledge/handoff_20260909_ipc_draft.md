# Archived incoming handoff — superseded interpretation

Preserved without editing the incoming text below. For current work and bounded
claims, use [handoff](handoff.md) and [IPC clarification](../docs/evaluation/phase5_pair_ipc_gpu_v1_review_addendum.md).

# Bàn giao phiên làm việc

Cập nhật: 2026-09-09. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase5 còn mở. User yêu cầu hoàn thiện tiếp trên main; tác vụ model lớn chỉ chạy
Kaggle. Không merge nhánh phase5-integration: [review đã lưu](phase5_integration_review_20260909.md).

Hiện tại: diagnostic IPC-origin `huylmhuhu/react-vn-pair-ipc-v1` đã COMPLETE.
Đã tải đầy đủ outputs vào `results/phase5_pair_ipc_gpu_v1_raw01`.
Chạy `scripts/audit_phase5_pair_ipc_gpu.py` hai lần độc lập vào `audit01` và `audit02`
cho kết quả byte-identical. Báo cáo kỹ thuật: [IPC GPU report](../docs/evaluation/phase5_pair_ipc_gpu_v1_report.md),
selected audit: [IPC audit manifest](../experiments/manifests/phase5_pair_ipc_gpu_v1_audit01.json).

Kết quả quan sát:
- Xác minh dứt điểm nguồn gốc 3 semaphore warnings: phát sinh từ `multiprocessing.synchronize.RLock`
  do `tqdm.std.create_mp_lock` khởi tạo khi Hugging Face nạp trọng số (`transformers.modeling_utils.from_pretrained`).
- Worker bị cưỡng chế dừng (SIGTERM/SIGKILL) khi hết timeout nên hook dọn dẹp của tqdm không kịp chạy.
- Residual VRAM phục hồi hoàn toàn (0 bytes trên cả 2 GPU across 18 samples).
- Không có rò rỉ VRAM hay CUDA driver.

## Bước tiếp theo

1. Thiết kế và triển khai kiểm thử quá tải ngữ cảnh (Context-Stress Test):
   Theo [Context-stress design](../docs/architecture/phase5_context_stress_v1_design.md)
   với đầu vào chính xác 4096 tokens, đầu ra 512/128 tokens để đo lường trần KV-cache trên Dual T4.
2. Vô hiệu hóa tqdm lock trong worker subprocess (`TQDM_DISABLE=1`) hoặc xử lý vòng đời
   để loại bỏ cảnh báo semaphore ở lần đóng thông dịch viên.
3. Tinh chỉnh prompt/cấu hình cho Guard Model nhằm khắc phục lỗi bỏ sót tấn công (under-triggering).
4. Thực hiện giao thức đánh giá đối sánh A0–A6 trên tập Dev (Grouped Dev Validation)
   để hoàn thành các chốt còn thiếu trước khi nghiệm thu Phase 5.
5. Chuyển tiếp sang Phase 6 (Evaluation Framework) và Phase 7 (Held-out Test Evaluation).


Pending access: không cần account/model access mới cho diagnostic hiện tại.
Account Kaggle huylmhuhu (kaggle1), CLI `python3 -m kaggle`2.2.4.
Dataset11942593 private/v1/ready; quota28,89h tại pre-submit2026-09-09, không phải
reservation/quota hiện tại. Kiểm lại trước run mới. Llama/Meta chưa chạy trong
pilot lịch sử; không ghi điểm0 hoặc suy quyền truy cập đã được cấp.

## Bằng chứng

- [IPC preflight](../experiments/manifests/phase5_pair_ipc_gpu_v1_preflight01.json):
  source9087791,15file overlay giữ13source cũ. Archive/expanded/PAX mỗi layout
  8tools/21Dummy/missing-only resume/three stub trials pass,90parent REGISTER/
  90UNREGISTER. CPU controls không phải GPU attribution.
- [IPC QA](../experiments/manifests/phase5_pair_ipc_gpu_v1_pre_submit_qa01.json):
  full1.481tests,51new (31tracer/wrapper+20audit). XML
  `results/phase5_pair_ipc_v1_pre_submit02_pytest.xml`.
- [Pair cancellation GPU report](../docs/evaluation/phase5_pair_cancel_gpu_v1_report.md):
  v1 COMPLETE/sourcee01b4e7/pre-pushf6474a7, ba fresh pairs,6loads/0generation,
  5TERMINATE/1KILL/0graceful;18VRAM samples residual0bytes haiGPU.
  91rawfiles, hai audit byte-identical;1.430tests pass. Warning3semaphores chưa
  attribution; [selected audit](../experiments/manifests/phase5_pair_cancel_gpu_v1_audit01.json).
- [Small-context pair GPU](pair_gpu_v1.md):
  v1 COMPLETE,2small calls,6recovery samples residual0bytes,62rawfiles,
  bothTERMINATE/not graceful. Không max-context/quality claim.
- [Guard-only cancellation](guard_cancellation_v1.md), [guard GPU](guard_gpu_probe_v1.md):
  giữ raw/failed graceful verdicts; guard B=SAFE và A/Boutputs giống nhau vẫn là
  quality limitation, không chốt Qwen1.5B production.
- Mốc CPU/nguồn cũ: [ModelPair](model_pair_v1.md),
  [pair cancellation](pair_cancellation_v1.md), [HF loader](agent_loader_v1.md),
  [mount authentication](agent_mount_v1.md), [placement](coexistence_placement_v1.md).
  146prior source entries/13overlay và62+91prior GPU raw hashes đã recheck.
  Original README mismatch/full-inventory rejection không bị sửa.

## Giới hạn

Phase1/clean_v1.1 Phase2/adversarial_v2 Phase3/Phase4 đã accepted theo phạm vi
và owner self-review waiver; Phase5 chưa accepted. Test seals chỉ hash-check.
Không benchmark model Dev/Test run mới trong Phase5; GPU probes là technical scope.
Không dùng số tests pass để suy phần trăm hoàn thành đồ án hoặc chất lượng LLM.

VRAM recovery, worker reap, graceful exit và IPC cleanup là bốn kết luận khác nhau.
Trace IPC chỉ quan sát Python entry points sau install; không cached aliases/
C-level registrations hoặc kết quả unlink của tracker/OS. Instrumentation và GC
checkpoint riêng làm thay đổi workload; không gộp timing với các lượt cũ.
Project memory không đi vào prompt; không credentials/private GT/Test payload/
hidden reasoning. Assistant self-review không phải independent human review.
