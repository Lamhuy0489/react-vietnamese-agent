# Prompt cho phiên sau

Cập nhật: 2026-11-21. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy, không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong, không có notebook
Kaggle nào chạy.

Trạng thái (21/11 tối): bài v3 đã chốt. Đang TRIỂN KHAI "BrokerGuard Chat" trên nhánh deploy/demo-v1 (đã push, chưa PR).
M0–M3 xong: lõi src/react_agent/demo/, UI Gradio, scripts/run_demo_app.py (--dry-run chạy được), kho sạch data/demo/,
docs/demo/README.md, requirements-demo.txt, tests/demo/. Đọc docs/project/deployment_plan_v1.md và docs/demo/README.md.
Không sửa pyproject.toml (nằm trong seal release_v2). Mail thật chỉ qua outbox sau send_email_mock + BrokerGuard cho qua +
người dùng xác nhận + allowlist + hạn mức.

Việc của phiên này:
1. Hỏi owner đã có Gmail App Password và .env.demo chưa; nếu có: owner bật OmniRoute, Claude bật proxy Gemini 8444 theo
   README, chạy app, gửi thử một thư thật tới địa chỉ của owner (M2), ghi kết quả.
2. Chạy vài câu lệnh trong data/demo/scenarios.md với Gemini ở cả V3 và A0, sửa trace_view/UI nếu hiển thị sai.
3. M5: hiện từng bước khi đang chạy (đọc trace theo thời gian thực), nút chạy lại ở chế độ kia, tổng duyệt.
4. Khi owner đồng ý: mở PR deploy/demo-v1 → main.
Việc soạn file đơn giản có thể giao Gemini qua proxy Antigravity 8045 (script gọi thẳng chat completions); agy CLI đang lỗi
": ping" sau bản cập nhật 21/11, đừng dùng agy -p trừ khi owner báo đã sửa. Luôn review và chạy test phần Gemini viết.

Để sau: sửa bài theo phản biện (phan bien*.md, Review Huy.docx ở root, chưa commit) và đồng bộ bản Việt.
Commit và PR không ghi Claude là đồng tác giả. Claude không viết, đọc hay giao việc viết văn bản/prompt tấn công hay
nội dung Test (tài liệu injection cho demo do owner/Minh viết); chỉ hạ tầng, số đếm và biên soạn.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
