# Prompt cho phiên sau

Cập nhật: 2026-11-05 03:20. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A, hướng A+B+C. Test-2 seal 1576b89a… (held-out, không dùng để chỉnh). Test v1 không chạy
lại, không sửa file trong manifest v1, pyproject.toml, requirements-dev.txt.

Đêm 05/11 Claude chạy qua đêm trên lamhuy8904: D2 vòng 1 (A1) và D2+G vòng 1 (A2) trên Dev E2
(handoff mục "Đang làm", decision log "D2 round 1 declared", "D2+G round 1 declared"). Việc đầu tiên:
đọc kết quả (results/rebuild_a/adv_dev_e2_d2_r1_qwen3_8b*, adv_dev_e2_d2g_r1_qwen3_8b*, log build/kaggle/d2*_1105.log),
so tiêu chí dừng (benign ≥ 105, side-effect ASR ghép cặp ≤ 27 /200); nếu Claude đã ghi bảng vào decision log
thì kiểm lại. Đạt → final_config_v2 (D2, D2+G, robustness). Chưa đạt → vòng 2 (≤3 vòng, khai báo trước).
Owner cần: review 100 câu RQ3 (data/clean/robustness_v1/authored_candidates.jsonl) để seal; merge PR #5 (CI xanh).
Sau đó: runner clean robustness, freeze v2, Test-2 1.000 lượt.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
