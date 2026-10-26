# Prompt cho phiên sau

Cập nhật: 2026-10-26 19:00. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A, R1 xong, R2 xong trên Dev. Chỉ số chính RQ2 là ASR ghép cặp
(attributable ASR): A0 26 → A3 15 → A4–A6 0 /200. A6 v3 accepted (benign 60/200, utility
under attack 40). Bảng Dev: A0–A5 từ results/rebuild_a/adv_dev_qwen3_8b_a6v2, A6 từ
results/rebuild_a/adv_dev_qwen3_8b_a6v3; chi tiết trong decision log ngày 2026-10-26.

Việc đầu tiên: hỏi owner duyệt đóng băng R3 (model, prompt v3, guard, A6 v3, evaluator có ASR
ghép cặp). Nếu duyệt thì cập nhật phase_status, rồi chuẩn bị R4 (chạy Test một lần).
Kiểm PR #4 đã merge và tag phase5-closure chưa.
Không sửa prompt v3, không đụng Test trước khi đóng băng, không sửa dữ liệu đã seal.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
