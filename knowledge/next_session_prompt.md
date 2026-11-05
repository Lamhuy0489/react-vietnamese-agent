# Prompt cho phiên sau

Cập nhật: 2026-11-05 15:10. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A xong toàn bộ lượt Test (05/11) dưới final_config_v2 (8889e448…): Test-2 1.000 lượt,
clean Test RQ1 + robustness RQ3 × Qwen3-8B, Llama-3.1-8B, Gemma-4-12B. Không chạy lại Test nào, không sửa file
trong manifest v1/v2, pyproject.toml, requirements-dev.txt. Số liệu ở decision log 2026-11-05 ("Test-2 result",
"Clean Test (RQ1) and clean robustness (RQ3) result").

Việc phiên này:
1. Hỏi owner cách trình bày Test-2: hai giả thuyết D2 đạt (D2 vs A0 ASR 17→0; D2 vs A6 benign 10→62) nhưng D2
   trùng A1 ở 200/200 lượt, nên Test-2 không cho thấy giá trị riêng của D2 (Dev: A1 27 → D2 14). Đề xuất báo
   nguyên trạng kèm giới hạn (5/20 family gây hại ở A0).
2. Soạn chương kết quả luận văn (RQ1, RQ2 v1 + Test-2, RQ3) từ các bảng trong decision log; hỏi owner định dạng
   và chỗ lưu trước khi viết dài.
3. R0: nếu owner đã merge PR #5, dọn script và test còn lại (hạn 2027-02-19).
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
