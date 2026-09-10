# Pair progress GPU v1 — đã audit, prevention gate đạt

Cập nhật 2026-09-10. [Contract](../docs/architecture/phase5_pair_progress_v1_contract.md).
Đã push nguồn/QA lên main `f8ab56d`, sau đó gửi đúng một kernel version 1,
COMPLETE. Handle `huylmhuhu/react-vn-pair-progress-v1`. Source tải về
`build/kaggle/pair_progress_gpu_v1_remote_source01`; 106 raw files trong
`results/phase5_pair_progress_gpu_v1_raw01`. Audits01/02 và reports byte-identical;
[selected audit](../experiments/manifests/phase5_pair_progress_gpu_v1_audit01.json),
[báo cáo](../docs/evaluation/phase5_pair_progress_gpu_v1_report.md).

Prevention gate đạt: sáu native worker policy receipts khớp PID/version/hash;
0 child registrations, owner 90/90, 0 unmatched, log không semaphore warning.
Sáu model loads, không generation; resident 9,799/7,621 GiB. Cả 18 recovery
samples residual 0 bytes hai GPU. 5 TERMINATE + 1 KILL, 0 graceful exits.
Không suy thành exhaustive IPC/driver cleanup hoặc native generation cancellation.
Không resubmit/overwrite hoặc local model load/Test payload. Không job còn chạy.
[Release QA](../experiments/manifests/phase5_pair_progress_gpu_v1_release_qa01.json):
1.552 pass/1 optional native skip, setup/Ruff/mypy248/knowledge đạt, 118 files
credential-value scan/0matches. Không suy full test count thành model quality.
Lượt mới kiểm chứng bản sửa thread-only progress lock với cùng Qwen 7B/1.5B,
image và ba ca cancellation. Không sửa kernel/nguồn/dữ liệu cũ.

Đã tạo entry/wrapper/builder riêng và auditor tái sử dụng IPC/HF integrity gates,
thêm policy receipts gắn PID và owner binding. CPU preflight dùng native tqdm
wheel 4.67.3 đã tải (78 kB), không tải model. Source `a1a90b3` đã qua cả hai
archive/expanded/PAX layouts: 8 tools, 21 Dummy, completed/missing-only resume,
6 native-policy workers/layout không registration và owner 90/90 cân bằng.
[Preflight receipt](../experiments/manifests/phase5_pair_progress_gpu_v1_preflight01.json)
bind 17 overlay files; 21 test mới đạt. Full QA: 1.517 đạt, 1 optional native
pytest bỏ qua trong 358,49s; native tqdm đã thực sự chạy riêng ở cả hai layouts.
Setup/Ruff/mypy 247 files/knowledge đạt; scan 31 source/payload files với bốn
credential values không có matches. [Pre-submit QA](../experiments/manifests/phase5_pair_progress_gpu_v1_pre_submit_qa01.json).
Chưa GPU submission tại mốc receipt này.

Lịch sử pre-submit: Account huylmhuhu có quota 28,57 giờ còn lại,
Dataset 11942593 ready/private/version 1 kiểm ngày 2026-09-10; không reservation.
Sau source/QA push, một submission `react-vn-pair-progress-v1`, T4,
timeout 5.400 giây bao gồm bootstrap và ba fresh pairs. Không đổi timeout/cap
trong protocol worker; không tự retry. Chưa model generation hoặc Phase 5 acceptance.

Tiếp: [context geometry](context_geometry_v1.md) đã có 35 tests và full QA
1.552 pass/1 native optional skip; cần native stress backend/runner, timing/cache/
memory instrumentation, exact GPU preflight riêng. Sau đó runtime integration,
A4/final scope và grouped Dev freeze. Không mở lại prevention diagnostic để
chạy lấy timing đẹp hơn hoặc gọi forced exits là graceful.
Giữ nguyên các báo cáo MD/PDF/figures ngoài task, không stage vào commit.
