# Pair progress GPU v1 — exact preflight đạt

Cập nhật 2026-09-10. [Contract](../docs/architecture/phase5_pair_progress_v1_contract.md).
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

Tiếp: receipt và push. Account huylmhuhu: quota 28,57 giờ còn lại,
Dataset 11942593 ready/private/version 1 kiểm ngày 2026-09-10; không reservation.
Sau source/QA push, dự kiến một submission `react-vn-pair-progress-v1`, T4,
timeout 5.400 giây bao gồm bootstrap và ba fresh pairs. Không đổi timeout/cap
trong protocol worker; không tự retry. Chưa model generation hoặc Phase 5 acceptance.
Giữ nguyên các báo cáo MD/PDF/figures ngoài task, không stage vào commit.
