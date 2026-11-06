# Prompt cho phiên sau

Cập nhật: 2026-11-06 15:25. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (06/11 15:25): Study 2. Dev v3 vòng 1 xong (27 cấu hình). Vòng chỉnh Dev 1 = D2+P2 (khai báo cc62bfa):
Gemma 2/48, Qwen3.5 3/48 family có hại (tốt nhất từ trước), benign_auth giảm (Qwen 36 → 24); Llama dừng 552/560.
AgentDojo-VI có tấn công (owner/Minh dịch, 54f366e) đang dở trên Llama. Máy owner tắt 15:25, notebook tự tắt khi idle.
Claude không viết, đọc hay giao việc viết đoạn chèn tấn công hay nội dung Test; chỉ làm hạ tầng và đọc số đếm.

Việc phiên này:
1. Kiểm kaggle kernels status 3 notebook serve (huylmhuhu Llama 16k, buiquocviet Gemma, oanhlam123456 Qwen3.5): đã tắt.
2. Resume Llama bằng lệnh trong handoff "Đang làm" (relaunch_round1.sh, có HF_TOKEN): chạy tiếp D2+P2 Llama và 6 lượt
   AgentDojo-VI có tấn công. Theo dõi bằng tiến trình chờ chạy nền; xong thì tắt keep-alive.
3. Ghi decision log: D2+P2 Llama, bảng AgentDojo VI so với EN (utility / attack success, 3 cấu hình × 2 suite).
4. Owner chọn vòng chỉnh 2 (khai báo trước): lớp cho M3–M5 và giảm chặn nhầm benign_auth của D2+P2.
5. Tầng 2 (Qwen3-8B, Qwen3.6-35B-A3B) và SecAlign-8B {A0, D2}; seal Dev/Test (tách oracle Test, seal.json bằng hash).
6. Nhắc owner: Test v3 phải do người viết; nếu có dùng công cụ AI thì ghi rõ trong decision log.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
