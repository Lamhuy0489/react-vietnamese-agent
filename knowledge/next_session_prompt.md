# Prompt cho phiên sau

Cập nhật: 2026-11-07 22:30. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (07/11 22:30): Study 2. Release v3 đã seal (cbfc549). Dev v3 xong hết: Tầng 1 vòng 1–2 (vòng 2 D2-NR+P2 bị bác;
D2+P2 là ứng viên chính: Gemma 2, Qwen3.5 3, Llama 5 /48), Tầng 2 Qwen3-8B và Qwen3.6-35B-A3B, SecAlign, AgentDojo-VI có
tấn công (decision log 07/11). release.py/evaluate_v3_v1.py đã ghi và nạp oracle theo split (private/test_oracles.json).
Không còn notebook nào chạy. Claude không viết, đọc hay giao việc viết đoạn chèn tấn công hay nội dung Test; chỉ làm hạ tầng
và đọc số đếm. Tài khoản GPU owner cho dùng: oanhlam123456, nomtle, dovuong05 (huylmhuhu, buiquocviet chỉ khi không có
notebook đang chạy).

Việc phiên này:
1. Hỏi owner: dùng vòng chỉnh 3 (cuối) hay chốt final_config_v3 = D2+P2. Nếu chốt: ghi decision log, ghim manifest
   final_config_v3, rồi chạy Test v3 một lần (A0 và D2+P2, các backbone đã khai báo); không chỉnh gì sau khi thấy số Test.
2. Bắt đầu bảng luận văn Study 2 từ decision log (Dev vòng 1–2, Tầng 2, SecAlign, AgentDojo-VI).
3. Dung lượng: owner chưa duyệt xoá build/venv_guard, build/kaggle/phase5_*, cache; nén results cũ ra ổ ngoài (xem handoff).
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
