# Prompt cho phiên sau

Cập nhật: 2026-11-05 01:05. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A, hướng A+B+C (decision log 2026-10-28). B xong, C xong (Test-2 seal 1576b89a…,
held-out, không dùng để chỉnh). Test v1 không chạy lại, không sửa file trong manifest v1, không sửa
pyproject.toml hay requirements-dev.txt.

E2 Dev mốc xong 2026-11-05 (decision log "E2 Dev re-baseline result": benign A0/A1 110, A6 60 /200;
tiêu chí dừng D2 benign ≥ 105, side-effect ASR ≤ 27 /200). Việc đầu tiên: D2: module luật đã có (control_data_policy_v1.py, handoff mục "D2 bắt đầu"); viết runtime_d2_v1 + runner,
chạy và chỉnh ≤3 vòng trên Dev E2, rồi final_config_v2. Song song: RQ3 250 biến
thể robustness. Kiểm PR #5 (sửa 21 test CI) đã xanh chưa, owner merge. Có thể giao việc phụ cho
Antigravity CLI (skill antigravity-subagent, Gemini 3.8 Flash), Claude review và chạy test.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
