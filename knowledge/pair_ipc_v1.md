# IPC-origin diagnostic — exact preflight và QA đã pass

Đính chính2026-09-10: [review addendum](../docs/evaluation/phase5_pair_ipc_gpu_v1_review_addendum.md)
là diễn giải hiện hành. Audit03/04 tái lập99raw files byte-identical; cả6worker
forced exit, dù3idle cóUNREGISTER. Không suy ra driver/IPC leak-free; không dùng
TQDM_DISABLE làm fix. [Bản sửa thread-only CPU](worker_progress_v1.md) tách riêng,
chưa GPU/runtime verification. Các diễn giải cũ phía dưới được giữ để đối chiếu.

Mốc trước: [pair cancellation](pair_cancellation_v1.md) GPU pass resource gates,
warning3semaphores chưa xác định nguồn. Không sửa hoặc thay thế kết quả cũ.

Kiểm tra log lịch sử trong lúc chờ diagnostic: guard-only cancellation cũng
warning2semaphores tại419,859s, raw
`results/phase5_guard_cancellation_v1_raw01/react-vn-guard-cancel-run-v1.log`.
Vì vậy không coi cảnh báo là đặc thù của ModelPair. Đây là quan sát log, chưa
creation-site attribution hoặc chứng minh persistent leak; không sửa receipt cũ.

[Contract](../docs/architecture/phase5_pair_ipc_v1_contract.md): diagnostic mới giữ
13overlay cũ, thêm tracer/entry point; không manual unregister/unlink, không đổi
grace, không model.generate. Trace chỉ PID/role/hash tên resource/metadata stack,
không locals/source text/prompt/credentials. Owner GC checkpoint được khai báo
riêng, không coi là sửa cleanup; tracker/OS unlink chưa được quan sát trực tiếp.

CPU prototype source chưa commit: `results/phase5_pair_ipc_cpu_dev01`, ba ca pass;
parent90register/90unregister,6stub workers zero registrations. Đây là development
check trước final source, không selected release hoặc bằng chứng GPU. Positive
control test giết một process tự sở hữu semaphore để xác minh unmatched/warning.

Source9087791 exact preflight đã pass archive/expanded/PAX,8tools/21Dummy/
missing-only resume/three stub trials,90parent REGISTER/90UNREGISTER mỗi layout.
[Receipt](../experiments/manifests/phase5_pair_ipc_gpu_v1_preflight01.json).
Full finalQA1.481tests/359,83s pass,51new (31tracer/wrapper+20audit);
setup/Ruff/mypy241files/knowledge pass.
[QA](../experiments/manifests/phase5_pair_ipc_gpu_v1_pre_submit_qa01.json).
Ngày2026-09-09 quota28,89h, Dataset11942593 private/version1/ready verified;
không phải quota reservation. Tiếp: push receipts rồi submit một private twoT4
identity pair-ipc-v1. Audit implementation đã có, chưa actual GPU attribution.

Đã push main 31910cb trước submit; kernel pair-ipc-v1/version1 đã COMPLETE.
Đã tải đầy đủ outputs về `results/phase5_pair_ipc_gpu_v1_raw01` và chạy
`scripts/audit_phase5_pair_ipc_gpu.py` hai lần độc lập vào `results/phase5_pair_ipc_gpu_v1_audit01`
và `audit02`, cho kết quả byte-identical.
[Selected audit](../experiments/manifests/phase5_pair_ipc_gpu_v1_audit01.json),
[Technical report](../docs/evaluation/phase5_pair_ipc_gpu_v1_report.md).

Kết quả xác minh nguồn gốc (conclusive root-cause attribution):
- Cảnh báo 3 leaked semaphore objects khớp chính xác 3 tiến trình worker bận bị
  cưỡng chế dừng (TERMINATE/-15 và KILL/-9).
- Trace call stack xác định toàn bộ semaphore được đăng ký bởi `multiprocessing.synchronize.RLock`
  gọi từ `tqdm.std.create_mp_lock` khi nạp trọng số mô hình qua `transformers.modeling_utils.from_pretrained`.
- Khi worker bị ngắt giữa chừng vì timeout, Python không kịp gọi cleanup hook của tqdm,
  dẫn tới resource tracker của tiến trình cha phát hiện semaphore mồ côi tại shutdown.
- Xác nhận VRAM phục hồi hoàn toàn (residual 0 bytes across 18 samples). Không có rò rỉ VRAM hay CUDA driver.
- Hướng xử lý vòng đời: có thể vô hiệu hóa tqdm lock trong worker subprocess (`TQDM_DISABLE=1`).
- Các chốt còn lại của Phase 5: context stress test (4096 input tokens), runtime integration, và grouped Dev validation.
