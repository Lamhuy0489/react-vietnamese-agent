# Prompt cho phiên sau

Cập nhật: 2026-10-28 06:10. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A. R4 security Test đã xong (2026-10-28, decision log có bảng; chạy một lần,
không chạy lại). PR #4 đã merge, tag phase5-closure đã gắn. Manifest final_config_v1 giữ nguyên.

Việc đầu tiên: RQ3 robustness. Tạo 250 biến thể clean (50 task gốc Test × 5 loại), không chấm
model nào trên chúng; review, seal, rồi đóng băng thành final_config_v2 (chỉ thêm input
robustness và đường runner/evaluator), dry-run Dummy.
Sau đó: clean Test + robustness cho Qwen, Llama, Gemma; mỗi backbone một notebook, chạy song song
trên các tài khoản còn quota (ghi vào decision log trước khi chạy), keepalive suốt đợt.
Việc phụ: PR riêng sửa 21 test chỉ hỏng trên CI. Không sửa file nào nằm trong manifest.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
