# Khóa tiến độ trong worker — CPU implementation

Cập nhật2026-09-10. [Contract](../docs/architecture/phase5_worker_progress_v1_contract.md).
Pair IPC GPU diagnostic đã COMPLETE;99raw files và audit03/04 tái lập selected
audit byte-identical. [Đính chính](../docs/evaluation/phase5_pair_ipc_gpu_v1_review_addendum.md):
5TERMINATE/1KILL/0graceful;3idle workers cóUNREGISTER nhưng không graceful.
90parent registrations được gỡ,3busy unmatched có stacktqdm RLock; warningcount3khớp.
18VRAM samples residual0bytes, không chứng minh driver/IPC cleanup hoàn hảo.

Triển khai mới `worker_progress_v1.py`: opt-in lazy factory chỉ daemon spawn
worker, trước torch/Transformers/tqdm khởi tạo. Pin4.67.3/stdhash đã đo; dùng
publicset_lock(threading.RLock), từ chối late/repeated/changed dependency.
Không manual unregister/unlink; không đổi deadline/model/decoding hoặc source cũ.

Native CPU prototype `results/phase5_worker_progress_cpu_dev01` dùng installed
systemPython3.11/tqdm4.67.3, không tải model: bốn fresh children
defaultTERM/disabledTERM/threadTERM/threadKILL, registrations1/1/0/0,
unregister0tất cả. Hai positive controls phát warning2; tracker chịu trách nhiệm
cleanup. Không coi prototype chưa final source là selected release.

15unit tests pass; optional native pytest test skip vì .venv không có tqdm.
Standalone native controls đã chạy bằng systemPython có pinned package; không
giấu skip hoặc tự cài dependency. Full suite đang chạy, cần ghi số liệu cuối.
Tiếp: commit source, hai native reproductions/freeze receipt, full QA và push.
Sau đó versioned GPU wrapper/entry/preflight để kiểm chứng cùng HF models;
chưa áp dụng fix vào kernel/runtime. Không jobGPU mới đang chạy.

Context-stress [design](../docs/architecture/phase5_context_stress_v1_design.md)
chưa implementation/launch. Runtime integration, A4 processing scope, general
private-record final entitlements và grouped Dev decision/freeze vẫn còn.
Không tune từ four-call guard diagnostic, không chuyển Phase6/7/Test.
