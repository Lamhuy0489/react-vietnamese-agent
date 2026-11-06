# Prompt cho phiên sau

Cập nhật: 2026-11-06 12:15. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (06/11 12:15): Study 2. Dev v3 vòng 1 XONG (3 backbone Tầng 1 × 9 cấu hình × 560 lượt) và AgentDojo EN Llama XONG;
bảng trong decision log 06/11 "WP7: kết quả Dev v3 vòng 1". P2 và D2+P1 giảm hại mạnh nhất; G1 (Prompt Guard 2) và MEL ≈ A0;
D2 và PRG chặn M1–M2 nhưng M3–M5 còn lọt; P1 phản tác dụng trên Qwen3.5; Llama nhiều OUTPUT_TRUNCATED. Đóng góp nghiên cứu:
knowledge/study2_contributions.md. Test v3: owner đã viết 72 family T3_xx, chưa commit, chưa seal. Claude không viết, đọc
hay giao việc viết đoạn chèn tấn công hay nội dung Test; chỉ làm hạ tầng và đọc số đếm.

Việc phiên này:
1. Kiểm kaggle kernels status 3 notebook serve 06/11 (huylmhuhu, buiquocviet, oanhlam123456): phải đã tự tắt.
2. Owner chọn vòng chỉnh Dev 1 (tối đa 3 vòng). Claude khai báo trong decision log TRƯỚC khi chạy. Đề xuất D2+P2 và một
   lớp cho M3–M5. Chạy trên 3 backbone Tầng 1 (keep-alive, khoá output, scripts/aggregate_v3_dev_v1.py tổng hợp).
3. Tầng 2: Qwen3-8B, Qwen3.6-35B-A3B × 9 cấu hình trên Dev; SecAlign-8B {A0, D2}.
4. Seal (hạ tầng do Claude làm, không đọc nội dung): tách oracle Test khỏi release_v3/private/oracles.json sang file riêng,
   tạo seal.json bằng hash cho Dev và Test. Owner/Minh review WP5 trước khi seal Dev.
5. Owner/Minh: dịch data/agentdojo_vi/injection_tasks.yaml và attacks.yaml, rồi chạy AgentDojo-VI có tấn công.
6. Nhắc owner: Test v3 phải do người viết; nếu có dùng công cụ AI thì ghi rõ trong decision log. Không chạy Test
   trước khi chốt final_config_v3.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
