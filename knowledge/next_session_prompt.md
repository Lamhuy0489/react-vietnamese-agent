# Prompt cho phiên sau

Cập nhật: 2026-10-26. Copy khối dưới đây vào chat mới (Claude Code hoặc Codex).
Cuối mỗi phiên, cập nhật lại khối này và [nhật ký phiên](session_log.md).

```text
Tiếp tục đồ án. Đọc theo thứ tự: AGENTS.md, knowledge/current_status.md,
knowledge/handoff.md, docs/project/roadmap_v2_rebuild.md, 5 mục cuối của
knowledge/session_log.md, và mục ngày 2026-10-23 trong docs/project/decision_log.md.

Đang ở R0 của lộ trình v2, mức rebuild A. A0 Dev baseline đã có (2026-10-26):
prompt v3 đóng băng (prompts/a0_rebuild.py), schema per_tool_v1, chấm --numfix.
Qwen3-8B smoke 12/20, Dev 79/150; Llama-3.1-8B smoke 8/20, Dev 59/150. Xem handoff
mục 0, knowledge/rebuild_a_runbook.md và decision log 2026-10-26.
Việc tiếp: Gemma-4-12B trên Kaggle (rủi ro cao trên T4), bake-off guard, A0–A6 Dev;
song song là phần dọn R0: PR merge vào main, tag phase5-closure, dọn script cũ,
docs/metrics_spec.md. Không sửa prompt v3 nữa trước R3.
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
