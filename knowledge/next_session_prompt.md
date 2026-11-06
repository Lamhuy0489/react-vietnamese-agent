# Prompt cho phiên sau

Cập nhật: 2026-11-07 01:05. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (07/11 01:05): Study 2. Vòng chỉnh Dev 1 D2+P2 xong cả 3 model Tầng 1 (Gemma 2, Qwen3.5 3, Llama 5 /48).
Đêm 07/11 chạy (khai báo decision log 07/11): Tầng 2 Qwen3-8B (dovuong05) và Qwen3.6-35B-A3B (oanhlam123456) × {A0,R1,PRG,D2},
SecAlign-8B (nomtle) × {A0,D2} trên Dev; AgentDojo-VI có tấn công trên Llama (huylmhuhu v4). Không dùng buiquocviet.
Claude không viết, đọc hay giao việc viết đoạn chèn tấn công hay nội dung Test; chỉ làm hạ tầng và đọc số đếm.

Việc phiên này:
1. kaggle kernels status 4 notebook (xem kaggle_resources 07/11); đếm result.json từng thư mục v3_dev_<cfg>_<key>.
   Lượt dở thì resume bằng lệnh trong handoff "Đang làm" (tier2_launch.sh / relaunch_round1.sh). Tắt keep-alive còn sót.
2. Tổng hợp aggregate_v3_dev_v1.py; ghi decision log: Tầng 2 (Qwen3-8B, Qwen3.6), SecAlign so Llama-3.1-8B cùng base,
   bảng AgentDojo VI so với EN (utility / attack success, 3 cấu hình × 2 suite).
3. Owner chọn vòng chỉnh 2 (khai báo trước): lớp cho M3–M5 và giảm chặn nhầm benign_auth của D2+P2.
4. Seal Dev/Test (tách oracle Test, seal.json bằng hash) sau khi owner xác nhận Test v3 do người viết; nếu có dùng công cụ AI
   thì ghi rõ trong decision log. Các file scripts/test_data_part*.py chưa commit; Claude không đọc.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
