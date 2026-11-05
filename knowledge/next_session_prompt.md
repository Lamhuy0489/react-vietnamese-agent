# Prompt cho phiên sau

Cập nhật: 2026-11-05 23:55. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: Study 1 xong. Study 2: spec v3 đã duyệt, WP2 xong. WP3: pilot_v3 (owner/Minh viết) qua QA; A0 lần 1 chưa qua
cổng (Qwen3-8B 2/12, Llama-3.1-8B 1/12 family; decision log 06/11). Claude không viết hay đọc đoạn chèn tấn công, và
không tự soi trace chẩn đoán đoạn chèn; chỉ đọc số đếm từ script.

Việc phiên này:
1. Nếu owner/Minh đã chỉnh pilot_canonicals.json: chạy build_v3_release.py check rồi qa. Sạch thì xóa
   data/adversarial/pilot_v3/, chạy write, commit.
2. Bật serve Qwen3-8B và Llama-3.1-8B (kiểm kaggle kernels status trước), chạy build/kaggle/v3_pilot_chain.sh với output
   mới (vd results/rebuild_b/v3_pilot2_A0_<K>), rồi báo cổng pilot.
3. Song song: AgentDojo-VI venv riêng, baseline phòng thủ (spotlighting, sandwich, PromptGuard 2, MELON, kiểu Progent).
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
