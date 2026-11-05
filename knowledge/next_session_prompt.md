# Prompt cho phiên sau

Cập nhật: 2026-11-05 10:20. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A, hướng A+B+C. Test-2 seal 1576b89a… (held-out, không dùng để chỉnh). Test v1 không chạy
lại, không sửa file trong manifest v1, pyproject.toml, requirements-dev.txt.

D2 và D2+G vòng 1 trên Dev E2 đã xong (decision log "D2 round 1 result", "D2+G round 1 result"): D2 benign 108,
side-effect ASR ghép cặp 14 /200, đạt tiêu chí dừng nên D2 đóng băng; D2+G trùng D2 (guard không chặn thêm).
Việc phiên này:
1. Owner review 100 câu RQ3 (data/clean/robustness_v1/authored_candidates.jsonl), Claude sửa theo góp ý rồi seal
   variants.jsonl (review_status → approved, hash).
2. Viết runner clean robustness (task_id biến thể → GT canonical), test bằng Dummy trên Dev.
3. Soạn final_config_v2 (ghim D2, D2+G, robustness), owner duyệt, dry-run Dummy trên Test-2.
4. Sau freeze: Test-2 1.000 lượt (A0, A1, A6, D2, D2+G), bật lại notebook Qwen + guard (đang COMPLETE).
Owner cần merge PR #5 (CI xanh).
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
