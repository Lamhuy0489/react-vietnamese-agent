# Prompt cho phiên sau

Cập nhật: 2026-10-26 20:15. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A. R3 đã đóng băng (tag final-config, manifest
configs/final/final_config_v1.json). Dry-run Dummy trên Test đã pass. Repo giữ public,
HF token giữ nguyên, luận văn để sau (owner quyết).

Việc đầu tiên: chạy R4 security Test (2.100 lượt, khoảng 4,5 giờ). Bật lại notebook Qwen +
guard (launch_vllm_serve_v1.py prepare với --hf-token-env, kaggle kernels push, discover), rồi
chạy lệnh R4 trong handoff bằng retry wrapper, chạy nền, cập nhật tiến độ mỗi 30 phút. Xong
thì chấm điểm và ghi bảng Test vào decision log. Test chỉ chạy một lần; chạy lại chỉ khi lỗi
hạ tầng.
Sau đó: tạo 250 biến thể robustness RQ3 (owner đã chọn), review, seal, final_config_v2.
Không sửa file nào nằm trong manifest.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
