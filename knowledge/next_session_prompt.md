# Prompt cho phiên sau

Cập nhật: 2026-10-23. Copy khối dưới đây vào chat mới (Claude Code hoặc Codex).
Cuối mỗi phiên, cập nhật lại khối này và [nhật ký phiên](session_log.md).

```text
Tiếp tục đồ án. Đọc theo thứ tự: AGENTS.md, knowledge/current_status.md,
knowledge/handoff.md, docs/project/roadmap_v2_rebuild.md, 5 mục cuối của
knowledge/session_log.md, và mục ngày 2026-10-23 trong docs/project/decision_log.md.

Đang ở R0 của lộ trình v2. Nếu owner vừa chạy notebook vLLM, đọc
knowledge/rebuild_a_runbook.md, giúp pin revision và đọc kết quả trong
results/rebuild_a/. Sau đó làm tiếp theo "Bước tiếp theo" trong handoff:
merge branch vào main qua PR, tag phase5-closure, dọn script cũ, viết
docs/metrics_spec.md, rồi dựng harness mới để chạy lại từ Phase 1
(mức rebuild A, mục 2b của lộ trình). Giữ Test khóa, không sửa dữ liệu đã seal.
Cuối phiên: cập nhật handoff, current_status, session_log và prompt này,
chạy make knowledge-check, rồi commit và push.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root, file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
