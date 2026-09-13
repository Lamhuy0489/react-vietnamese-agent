# Pair/runtime v2 — lỗi sau response và failed-startup timing

Cập nhật 2026-09-13. Đã đạt bounded CPU QA; không có inference LLM/Kaggle/Test mới.

## Thay đổi

Giữ nguyên source/receipt CPU02 v1. Bản v2 giữ interface, runtime v7, policy,
prompt, decoding và tools. Thêm khoảng event cho mỗi host proposal để nối đúng
worker response với pair outcome; thêm `startup_completed` và elapsed thực tế
ngay cả khi load thất bại hoặc bị hủy trong startup.

Test dùng process thật: dừng agent hoặc guard ngay sau response của mỗi role;
worker có thể OK nhưng pair ERROR vì kiểm liveness sau response. Không sửa
worker status thành ERROR và không coi response bị loại là thành công của agent.
Auditor v1 tái hiện false rejection trên các case này; auditor v2 yêu cầu event
ERROR tương ứng, role/error class đúng, không trùng hay bỏ sót generation event.

## Xác minh

16 focused failure/timing/corruption tests ban đầu pass/17,43s. Lượt chính thức
64 integration tests pass/70,69s; 63 joined receipts đều audit đạt. Full repository
QA **2.560 pass/1 native-tqdm skip**, 551,55 giây. Setup/Ruff/mypy 320 files và
knowledge-check đạt. Audit độc lập khớp 445 source/641 raw hashes, 169 tracked
data hashes không đổi; 971 entries của CPU02 v1 vẫn khớp.
Validator: `scripts/verify_phase5_pair_runtime_v2.py`; output mới dự kiến
`results/phase5_pair_runtime_v2_cpu01`, không ghi đè CPU02 v1.

[Receipt](../experiments/manifests/phase5_pair_runtime_v2_cpu01.json) SHA-256
`0832ae8c29f925f8bc522ac3138fa6d41132d3dae53ac68d44ffd7bd58a453b9`.
Working-tree QA anchored parent `817da23`, không gọi clean-source/native release.
Không có job còn chạy. [Báo cáo](../docs/evaluation/phase5_pair_runtime_v2_report.md).

Có chín worker-OK/host-ERROR observations (bốn fault combinations và năm mutation
controls dùng lại một fault setup), không gọi là chín failure mechanisms độc lập.
Năm incomplete startups có elapsed 0,526–1,112s trên synthetic CPU backends;
không phải load latency của model thật. 90 GRACEFUL/13 TERMINATE/9 EXITED,
tất cả handles được đóng; EXITED gồm process bị test chủ động dừng.

## Tiếp theo và giới hạn

Sau mốc này, tiếp exact
archive/expanded Kaggle preflight với entry point v2 và equivalent native
agent-only factory. Guard quality/grouped Dev, broader semantic coverage và
freeze còn mở. Không thay trạng thái nghiệm thu Phase 5 từ test count.

[Contract](../docs/architecture/phase5_pair_runtime_v2_contract.md) ·
[CPU02 lịch sử](phase5_pair_runtime_v1.md) · [Handoff](handoff.md).
