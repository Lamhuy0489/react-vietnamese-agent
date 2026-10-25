# Prompt cho phiên sau

Cập nhật: 2026-10-26. Copy khối dưới đây vào chat mới (Claude Code hoặc Codex).
Cuối mỗi phiên, cập nhật lại khối này và [nhật ký phiên](session_log.md).

```text
Tiếp tục đồ án. Đọc theo thứ tự: AGENTS.md, knowledge/current_status.md,
knowledge/handoff.md, docs/project/roadmap_v2_rebuild.md, 5 mục cuối của
knowledge/session_log.md, và mục ngày 2026-10-23 trong docs/project/decision_log.md.

Đang ở R0 của lộ trình v2, mức rebuild A. A0 Dev baseline (prompt v3 đóng băng,
per_tool_v1, --numfix): Qwen3-8B smoke 12/20, Dev 79/150; Llama-3.1-8B smoke 8/20, Dev 59/150;
Gemma-4-12B smoke 9/20, clean Dev có thể còn dở. Việc đầu tiên: kiểm tra
results/rebuild_a/clean_dev_gemma4_12b_v3_pertool (đủ 150 task chưa), nếu thiếu thì làm theo
mục "Tiếp tục Gemma Dev" trong handoff, chấm --numfix, thêm hàng Gemma vào decision log.
Kiểm tra PR #4 đã merge và tag phase5-closure chưa. Sau đó: dọn script cũ, R1 evaluator,
chuẩn bị A0–A6 Dev (guard A2 = Llama-3.2-3B). Không sửa prompt v3.
Giữ Test khóa, không sửa dữ liệu đã seal.
Cuối phiên: cập nhật handoff, current_status, session_log và prompt này,
chạy make knowledge-check, rồi commit và push.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root, file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
