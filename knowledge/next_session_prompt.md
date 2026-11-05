# Prompt cho phiên sau

Cập nhật: 2026-11-05 23:55. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: Study 1 xong. Study 2: spec v3 đã duyệt (`1547dc4e…`), WP2 xong (3 backbone mới qua smoke).
WP3: pilot_canonicals.json 12/12 và release pilot_v3 đã build (check/qa 40 replays, 0 problems, max novelty 0.037 <= 0.20),
báo cáo review 5 mục docs/benchmark/pilot_v3_review_report.md đạt 100%, runner và evaluator v3 qua dry-run và 10 unit tests.

Việc phiên này:
1. Chạy A0 trên Qwen3-8B và Llama-3.1-8B cho pilot_v3 khi có GPU Kaggle (mục tiêu >= 40% ASR ở baseline).
2. Chuẩn bị viết Dev 48 và Test 72 với đủ 5 biến thể theo AUTHORING_GUIDE.md.
3. Merge PR #5 trên GitHub để sửa 21 test CI.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
