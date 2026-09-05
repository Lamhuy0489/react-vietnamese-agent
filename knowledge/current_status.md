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

## Trạng thái chất lượng

- Local Replay: 20/20 success, 20/20 terminal, 0 crash, 8/8 tool coverage.
- Real model: 20/20 terminal, 0 crash, 3/20 task success, 78,87% schema
  validity; đây là smoke metric, không phải kết quả luận văn.
- Test: 35/35 pass; package coverage 89%; Ruff và mypy strict pass.
- Held-out Test: chưa tạo và chưa truy cập.

## Tiếp theo

Phase 2 chưa bắt đầu. Khi chủ dự án cho phép, đọc `plan/phase2.md` và xây clean
benchmark theo contract; không dùng kết quả held-out Test để chỉnh prompt,
policy, threshold hay kiến trúc.
