# Prompt cho phiên sau

Cập nhật: 2026-11-05 16:30. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: Study 1 (rebuild A) xong hết lượt Test dưới final_config_v2; không chạy lại, không sửa file ghim.
Test-2 cho D2 = A1 (200/200) vì cả 20 family cùng một cơ chế mà regex A1 bắt được. Owner muốn nâng lên mức
hội nghị top: đề xuất Rebuild B / Study 2 ở docs/project/rebuild_b_proposal.md (chưa duyệt).

Việc phiên này:
1. Hỏi owner kết quả review đề xuất (mục 11: 6 quyết định). Chưa sinh dữ liệu hay sửa code trước khi duyệt.
2. Khi đã duyệt: ghi decision log, viết spec ma trận v3 (taxonomy M1–M6 + B-auth) và commit spec trước khi sinh
   dữ liệu; xác minh Qwen3.5-9B và Meta-SecAlign-8B trên HF, thử serve trên T4.
3. R0: nếu owner đã merge PR #5 thì dọn script và test còn lại.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
