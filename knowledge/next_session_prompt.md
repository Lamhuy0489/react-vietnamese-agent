# Prompt cho phiên sau

Cập nhật: 2026-11-06 11:05. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (06/11 11:05): Study 2. Dev v3 vòng 1 XONG: 3 backbone Tầng 1 × 9 cấu hình × 560 lượt, bảng trong decision log 06/11
"WP7: kết quả Dev v3 vòng 1" (P2 và D2+P1 giảm hại mạnh nhất; G1, MEL ≈ A0; D2/PRG chặn M1–M2, M3–M5 còn lọt; Llama nhiều
OUTPUT_TRUNCATED). AgentDojo EN Llama xong (số trong decision log). Claude không viết, đọc hay giao việc viết đoạn chèn tấn công.

Việc phiên này:
1. Kiểm kaggle kernels status: các notebook serve 06/11 phải đã tắt (hết keep-alive khoảng 12:20).
2. Cùng owner chọn vòng chỉnh Dev (tối đa 3, khai báo trước trong decision log trước khi chạy), ví dụ D2+P2, xử lý M3–M5.
3. Tầng 2 (Qwen3-8B, Qwen3.6-35B-A3B) và SecAlign {A0, D2} trên Dev.
4. Owner/Minh: WP5 review và seal Dev; dịch injection_tasks.yaml + attacks.yaml cho AgentDojo-VI có tấn công.
5. Nhắc owner: Test v3 phải tự viết tay, không dùng Antigravity hay model ngoài; Claude không đọc scripts/test_data_part*.py.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
