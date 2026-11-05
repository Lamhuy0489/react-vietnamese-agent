# Prompt cho phiên sau

Cập nhật: 2026-11-05 23:48. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: Study 1 xong. Study 2: spec v3 đã duyệt (1547dc4e…), WP2 xong (3 backbone mới qua smoke).
WP3: pilot_canonicals.json 12/12 đã tạo, check và qa sạch (40 replays, 0 problems, max novelty 0.037 <= 0.20),
đã write data/adversarial/pilot_v3, unit tests release.py đạt.

Việc phiên này:
1. Review chéo 12 họ pilot theo phiếu 5 mục ở taxonomy.md §7.
2. Viết runner scripts/run_v3_api_v1.py và khai báo metric M5 (side_effect_harm_v3) trong decision log trước khi chạy.
3. Chạy A0 trên Qwen3-8B và Llama-3.1-8B cho pilot_v3 (mục tiêu >= 40% ASR ở baseline).
4. Chuẩn bị viết Dev 48 và Test 72 với đủ 5 biến thể.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
