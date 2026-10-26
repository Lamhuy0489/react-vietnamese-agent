# Prompt cho phiên sau

Cập nhật: 2026-10-26 13:00. Copy khối dưới đây vào chat mới (Claude Code hoặc Codex).
Cuối mỗi phiên, cập nhật lại khối này và [nhật ký phiên](session_log.md).

```text
Tiếp tục đồ án. Đọc theo thứ tự: AGENTS.md, knowledge/current_status.md,
knowledge/handoff.md, docs/project/roadmap_v2_rebuild.md, 3 mục cuối của
knowledge/session_log.md, và các mục 2026-10-26 trong docs/project/decision_log.md.

Rebuild A: R1 xong, R2 khoảng 75%. A0 Dev baseline (prompt v3, name-first, numfix):
Qwen 77, Llama 93, Gemma 99 /150. A6 v2 đã accepted trên replay (benign 20 → 115/200, harm 5/200).
Lượt A0–A6 Dev đầy đủ (Qwen3-8B, A6 v2, guard Llama-3.2-3B, 2.800 lượt) bắt đầu resume
2026-10-26 12:23 tại results/rebuild_a/adv_dev_qwen3_8b_a6v2.
Việc đầu tiên: đếm runs/A*/*/result.json. Nếu < 2.800 thì chạy lại lệnh resume trong handoff
(bật lại notebook nếu đã tắt; không tự suy ra endpoint còn sống). Rồi chấm điểm, kiểm
model_error < 2%, ghi bảng A0–A6 vào decision log, cân nhắc đóng băng config (R3).
Kiểm PR #4 đã merge và tag phase5-closure chưa. Không sửa prompt v3, không đụng Test,
không sửa dữ liệu đã seal.
Cuối phiên: cập nhật handoff, current_status, session_log và prompt này,
chạy make knowledge-check, rồi commit và push.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root, file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
