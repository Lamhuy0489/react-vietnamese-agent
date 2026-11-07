# Prompt cho phiên sau

Cập nhật: 2026-11-07 11:35. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (07/11 11:35): Study 2. Release v3 đã seal (cbfc549). Vòng chỉnh Dev 2 (D2-NR+P2) bị bác; D2+P2 là ứng viên chính
(Gemma 2, Qwen3.5 3, Llama 5 /48). Tầng 2 Qwen3-8B và SecAlign xong; AgentDojo-VI có tấn công xong (decision log 07/11).
Còn Qwen3.6-35B-A3B Tầng 2 chạy trên oanhlam123456 v3. Claude không viết, đọc hay giao việc viết đoạn chèn tấn công hay nội
dung Test; chỉ làm hạ tầng và đọc số đếm. Tài khoản GPU owner cho dùng: oanhlam123456, nomtle, dovuong05 (huylmhuhu,
buiquocviet chỉ khi không có notebook đang chạy).

Việc phiên này:
1. kaggle kernels status oanhlam123456 Qwen3.6; đếm result.json v3_dev_{A0,R1,PRG,D2}_qwen36_35b_a3b_awq. Dở thì resume theo
   handoff "Đang làm"; xong thì aggregate_v3_dev_v1.py, ghi decision log Tầng 2 Qwen3.6, tắt keep-alive.
2. Khi không còn runner v3: sửa release.py write (oracle theo split, từ chối khi đã seal) và thêm test.
3. Hỏi owner: dùng vòng chỉnh 3 (cuối) hay chốt final_config_v3 = D2+P2; nếu chốt thì ghim manifest rồi chạy Test v3 một lần
   (nạp private/test_oracles.json).
4. Bắt đầu bảng luận văn Study 2 từ decision log (Dev vòng 1–2, Tầng 2, SecAlign, AgentDojo-VI).
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
