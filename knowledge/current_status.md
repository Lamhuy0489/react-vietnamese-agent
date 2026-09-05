# Trạng thái hiện tại

Cập nhật: 2026-09-05.

## Đã hoàn thành

- Setup repository, GitHub riêng tư và CI.
- Phase 0: research contract và các quyết định nền tảng.
- Phase 1: A0 baseline, simulated university environment, 8 mock tools, 20
  smoke tasks, trace JSONL, local Replay/Dummy và real-model Kaggle smoke.
- Kaggle authoritative run: kernel v4, Dataset v5, Qwen2.5-3B-Instruct v1,
  NVIDIA T4, internet tắt.
- Minh review được chủ dự án cho phép hoãn; lời mời GitHub vẫn giữ nguyên.
- Phase 2: clean benchmark 250 task, clean environment, split 150 Dev / 100
  Test, checksum/manifest và Dev-only Kaggle pilot.

## Trạng thái chất lượng

- Local Replay: 20/20 success, 20/20 terminal, 0 crash, 8/8 tool coverage.
- Real model: 20/20 terminal, 0 crash, 3/20 task success, 78,87% schema
  validity; đây là smoke metric, không phải kết quả luận văn.
- Test local: 47/47 pass; package coverage 83%; Ruff và mypy strict pass.
- Phase 2 oracle: 250/250; automated QA: 250/250; tool coverage đủ 8/8.
- Kaggle Dev pilot v2: 21/21 terminal, 0 crash, 334 trace hợp lệ, 7/21 task
  success; worker đọc 0 Test và 0 private ground truth.
- Held-out Test: đã niêm phong, chưa chạy model và không được dùng để tuning.

## Trạng thái phase

Phase 2 đã đạt acceptance trên branch `phase-2/clean-benchmark-v1`. Phase 3
chưa bắt đầu; cần chỉ thị rõ trước khi chuyển scope.

Huy và Minh dùng chung máy nên chủ dự án bỏ peer review. Dataset không ghi giả
reviewer; thay vào đó dùng automated QA 100% theo owner waiver, đồng thời ghi
rõ hạn chế thiếu independent human review trong data card. Không ghi rằng chủ
dự án đã inspect từng task; audit record dùng `automated_gate`.
