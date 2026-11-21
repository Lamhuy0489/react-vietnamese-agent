# Prompt cho phiên sau

Cập nhật: 2026-11-21. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy, không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong, không có notebook
Kaggle nào chạy.

Trạng thái (21/11): bài v3 đã chốt (main đủ, PR #8, #9). Giai đoạn hiện tại: TRIỂN KHAI THỰC TẾ "BrokerGuard Chat",
nhánh deploy/demo-v1. Đọc docs/project/deployment_plan_v1.md (quyết định Q1–Q10, bước M0–M5) và decision log 2026-11-21.
Owner đã chốt: giao diện Gradio, gửi mail thật qua Gmail SMTP + App Password theo mô hình hộp thư chờ (agent vẫn gọi
send_email_mock không đổi; lớp demo gửi sau khi BrokerGuard cho qua + người dùng bấm xác nhận + allowlist + hạn mức,
DEMO_EMAIL_LIVE mặc định 0). Không thêm tool gửi mail tên mới vì BrokerGuard nhận sink theo tên.

Việc của phiên này:
1. M0: .env.demo.example (chỉ tên biến), thêm !.env.demo.example vào .gitignore, nhóm phụ thuộc demo (gradio,
   python-dotenv) trong pyproject.toml, chuyển khóa OmniRoute viết cứng trong scripts/run_gemini_smoke.py sang env.
2. M1: lõi src/react_agent/demo/ (config, corpus, session, trace_view) kèm tests/demo/, chạy được A0 và v3 với
   --dry-run-dummy. Không sửa file pinned (final_config_v5 phải còn khớp hash).
3. Hỏi owner đã có Gmail gửi (2FA, App Password) và danh sách địa chỉ nhận chưa, để làm M2.
Trước khi xong: ruff, mypy src scripts, pytest, verify_setup.

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
