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

## Mốc CPU đã kiểm chứng

Hai lượt `results/phase5_worker_progress_cpu_validation01` và `validation02`
chạy từ source `e8f72de5f5ff9c9406f981db99834a60fd62652c`, system Python 3.11.0,
tqdm 4.67.3. Cùng registrations 1/1/0/0, unregister 0/0/0/0; 8 PID khác nhau,
tất cả reaped với exitcodes -15/-15/-15/-9 mỗi lượt. Mỗi lượt giữ 7 raw files
và warning 2 semaphore của positive controls; không manual cleanup hoặc che lỗi.
Source hashes khớp; PID/raw bytes khác nhau được giữ riêng, không ép byte parity.
[Selected receipt](../experiments/manifests/phase5_worker_progress_v1_validation01.json)
khớp nguyên byte receipt lượt 01; lượt 02 được bind hash trong
[release QA](../experiments/manifests/phase5_worker_progress_v1_release_qa01.json).

Full suite: 1.496 đạt, 1 bỏ qua trong 354,52s (JUnit 354,450s), gồm 15 unit mới.
Optional native pytest bỏ qua vì .venv thiếu tqdm; hai standalone native runs
ở trên đã thực sự chạy với package pin, không tính skip thành pass.
Setup/Ruff/mypy 243 files/knowledge đạt. 146 frozen source entries,
13 cancellation + 15 IPC overlay hashes, 91 + 99 GPU raw hashes và Test seals
hash-only được kiểm lại nguyên vẹn. Không model load hoặc Kaggle submission mới.

Tiếp theo: versioned GPU wrapper/entry/preflight để kiểm chứng cùng HF models;
chưa áp dụng fix vào kernel/runtime. Không job local/Kaggle còn chạy.

Context-stress [design](../docs/architecture/phase5_context_stress_v1_design.md)
chưa implementation/launch. Runtime integration, A4 processing scope, general
private-record final entitlements và grouped Dev decision/freeze vẫn còn.
Không tune từ four-call guard diagnostic, không chuyển Phase6/7/Test.
