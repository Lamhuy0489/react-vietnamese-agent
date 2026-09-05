# Bằng chứng Phase 1

## Run được chấp nhận

- Source commit: `2138dc83bfbbe5d38885418255a72238f5c33357`.
- Kernel: `huylmhuhu/react-vietnamese-agent-phase-1-real-model-smoke`, version 4.
- Dataset: `huylmhuhu/react-vietnamese-agent-phase1-bundle`, version 5.
- Bundle SHA-256: `39f1e63ddca56e4dd8cf4b5949927b250017e7f2875e55cbf0b1f7b4422dddc9`.
- Model: `qwen-lm/qwen2.5/transformers/3b-instruct/1`.
- T4, internet disabled, temperature 0, seed 42.
- Manifest máy đọc được: `experiments/manifests/phase1_kaggle_v4.json`.

## Acceptance

- 20/20 real-model trajectories có terminal status; 0 model/process crash.
- 262/262 trace events hợp lệ theo Pydantic; mọi tool call đúng thứ tự
  proposed → executed → result.
- Local Replay bao phủ đủ 8 tools và đạt 20/20 task success.
- Real model gọi 6 tools, hoàn thành 16 run, có 2 max-step và 2 parse-failure;
  3 task đạt expected behavior.
- Quét artifact bằng chính giá trị bí mật từ bốn credential local: 0 match.
- Không có side effect thật và không truy cập held-out Test.

Raw artifacts được giữ local tại `results/phase1/kaggle_v4/` và bị Git ignore.
Các hash trong manifest cho phép kiểm tra artifact tải lại từ Kaggle.

## Cách hiểu kết quả

Phase 1 chứng minh pipeline chạy end-to-end, không đặt mục tiêu accuracy cao.
Điểm 3/20 cho thấy Qwen2.5-3B A0 còn yếu ở chọn tool, tạo SQL/arguments và tuân
thủ JSON khi gặp sink task. Đây là limitation cần giữ nguyên, không được chạy
lại chỉ để chọn kết quả đẹp hơn.
