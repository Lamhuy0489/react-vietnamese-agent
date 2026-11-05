# Prompt cho phiên sau

Cập nhật: 2026-11-06 02:50. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (06/11 02:50): Study 2. WP3 pilot đạt (lần 5, Qwen3-8B 6/12, decision log 06/11). Dev v3 48 family / 560 fixture
qua QA. WP7 đang chạy Dev × 9 cấu hình (A0, D2, R1, PRG, P1, G1, MEL, P2, D2P1) trên Gemma-4-12B (buiquocviet), Llama-3.1-8B 16k
(huylmhuhu, chung endpoint AgentDojo), Qwen3.5-9B (oanhlam123456), có keep-alive tới khoảng 12:00 06/11. Claude không viết, đọc
hay giao việc viết đoạn chèn tấn công; chỉ đọc số đếm.

Việc phiên này:
1. Kiểm kaggle kernels status 3 notebook và log build/kaggle/v3_dev_chain_<K>.log, agentdojo_chain_llama31_8b.log.
   Lượt nào dở thì chạy lại cùng lệnh chuỗi (resume theo result.json); cần service Prompt Guard cho G1.
2. Khi đủ: tổng hợp bảng Dev (ASR theo cơ chế M1–M6, utility benign_plain và benign_auth, false block) cho 3 backbone × 9
   cấu hình; ghi decision log (Dev, vòng 1). Đề xuất vòng chỉnh (tối đa 3, khai báo trước), không đụng Test.
3. AgentDojo: tổng hợp utility/ASR EN và VI-utility của Llama. Owner/Minh dịch injection_tasks.yaml và attacks.yaml thì chạy VI
   có tấn công. Gemma cần key context dài hơn (thử bản QAT).
4. Nhắc owner: Test v3 phải tự viết tay, không dùng Antigravity hay model ngoài (scripts/test_data_part*.py chưa commit).
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
