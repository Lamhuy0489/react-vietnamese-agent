# Prompt cho phiên sau

Cập nhật: 2026-11-21. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy, không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong, không có notebook
Kaggle nào chạy.

Trạng thái (22/11): bài v3 đã chốt. Đang làm ứng dụng demo BrokerGuard Workspace trên nhánh deploy/demo-v1, thư mục
webapp/ (đọc webapp/README.md và docs/project/app_design_v2.md). Đã có W1 (đăng nhập argon2id, phiên, CSRF, khóa, mã mời,
4 vai trò) và khung W3 (React/Vite/TS, sáng/tối, Login/Invite/Home/Conversation 3 cột chạy bằng src/mocks). Lõi agent:
src/react_agent/demo/ (session, trace_view, outbox, gmail_sender); .env.demo đã điền. Không sửa pyproject.toml gốc (seal).

Việc của phiên này:
1. Hỏi owner góp ý giao diện (owner chạy create-admin, make webapp-build, make webapp-serve, mở 127.0.0.1:8000).
2. W2: routers conversations, turns (chạy DemoSession trong thread), events SSE (đọc trace_security.jsonl khi đang chạy),
   sources, outbox (send chỉ admin/presenter, ghi audit); lưu messages vào SQLite; test quyền và SSE. Nối frontend bỏ mocks.
3. Ghi rõ trạng thái thư trong câu trả lời (thư còn chờ xác nhận, không phải "đã gửi").
Giao việc giao diện cho Gemini qua proxy Antigravity 8045 (scratchpad tools/ag_call.py; nếu proxy tắt: open -a
"Antigravity Tools"); agy -p đang lỗi. Luôn review, build và test phần Gemini viết. Không emoji/biểu tượng, không
chain-of-thought.

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
