# Prompt cho phiên sau

Cập nhật: 2026-11-05 17:30. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: Study 1 (rebuild A) xong, giữ nguyên, không chạy lại, không sửa file ghim. Owner đã duyệt Study 2
(Rebuild B, nhắm hội nghị quốc tế về LLM/an toàn agent): kế hoạch docs/project/rebuild_b_plan.md (WP0 xong).

Việc phiên này:
1. WP1: viết spec v3 (data/adversarial/v3_authoring/spec.json + taxonomy.md + validator) theo mục 3 của kế hoạch;
   trình owner duyệt rồi ghi hash vào decision log trước khi sinh dữ liệu.
2. WP2: xác minh trên HF Qwen3.5-9B, Qwen3.6-35B-A3B (bản 4-bit), Meta-SecAlign-8B; viết backbones_v3.yaml;
   bật notebook và smoke 20 task trên T4 (kiểm kaggle kernels status và quota trước).
3. Nếu owner đã merge PR #5 thì dọn R0.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
