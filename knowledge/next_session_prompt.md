# Prompt cho phiên sau

Cập nhật: 2026-11-05 01:05. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A, hướng A+B+C (decision log 2026-10-28). B xong, C xong (Test-2 seal 1576b89a…,
held-out, không dùng để chỉnh). Test v1 không chạy lại, không sửa file trong manifest v1, không sửa
pyproject.toml hay requirements-dev.txt.

Đêm 2026-11-05 đã chạy E2 Dev mốc A0 → A1 → A6 × 400 trên lamhuy8904 (Qwen v5 + guard v3), kết quả
results/rebuild_a/adv_dev_e2_qwen3_8b, chấm tự động bằng build/kaggle/e2_eval_after_run.sh (log
build/kaggle/e2_dev_eval_1105.log). Việc đầu tiên: kiểm log runner và log chấm (đủ 1.200 lượt? lỗi?),
nếu thiếu thì chạy lại lệnh resume trong handoff; rồi ghi bảng E2 so với Dev v1 (cả hai evaluator) vào
decision log. Sau đó viết D2 và chỉnh ≤3 vòng trên Dev E2, rồi final_config_v2. Song song: RQ3 250 biến
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
