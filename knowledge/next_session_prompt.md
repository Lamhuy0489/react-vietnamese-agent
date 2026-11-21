# Prompt cho phiên sau

Cập nhật: 2026-11-21. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy, không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong, không có notebook
Kaggle nào chạy.

Trạng thái (22/11): bài v3 đã chốt. Đang làm ứng dụng demo trên nhánh deploy/demo-v1. v1 (Gradio, lõi
src/react_agent/demo/) chạy được với Gemini; .env.demo đã điền (Gmail gửi, allowlist). Owner muốn thay Gradio bằng ứng
dụng web hoàn chỉnh: đọc docs/project/app_design_v2.md (bố cục kiểu NotebookLM, 4 vai trò, design tokens sáng/tối, API,
W1–W6) và decision log 2026-11-22.

Việc của phiên này:
1. Hỏi owner đã duyệt app_design_v2.md chưa (vai trò, màu, bố cục); sửa theo góp ý.
2. W1: src/react_agent/webapp/ (main, db, auth argon2id, roles), scripts/webapp_admin.py create-admin, tests/webapp/.
   Thêm fastapi, uvicorn, argon2-cffi vào requirements-demo.txt (không sửa pyproject.toml: seal release_v2).
3. W3 song song: giao Gemini qua proxy Antigravity 8045 (script ag_call gọi thẳng chat completions, agy -p đang lỗi)
   dựng web/ React + Vite + TS theo tokens mục 5; Claude review, chạy lint/build.
Không hiện chain-of-thought, chỉ hành động và quyết định cổng. Không emoji/biểu tượng trong giao diện.

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
