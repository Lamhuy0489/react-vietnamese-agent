# Prompt cho phiên sau

Cập nhật: 2026-11-05 19:00. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: Study 1 xong, giữ nguyên. Study 2 (docs/project/rebuild_b_plan.md): WP1 spec v3 đã viết
(data/adversarial/v3_authoring/spec.json, sha256 1547dc4e…, taxonomy.md), CHỜ OWNER DUYỆT; WP2 đã thêm 3 model
key (qwen35_9b, qwen36_35b_a3b_awq, secalign_8b) nhưng chưa smoke trên T4.

Việc phiên này:
1. Hỏi owner đã duyệt spec chưa (và đã xin quyền HF facebook/Meta-SecAlign-8B chưa). Duyệt thì ghi decision log kèm
   hash, rồi mới viết câu lệnh pilot.
2. WP2: kiểm kaggle kernels status và quota, bật qwen35_9b, smoke 20 task (lệnh trong Bản đồ runbook), ghi kết quả;
   rồi qwen36_35b_a3b_awq; SecAlign khi có quyền.
3. WP3: viết 12 family pilot theo spec, chạy A0 trên Qwen3-8B và Llama-3.1-8B.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
