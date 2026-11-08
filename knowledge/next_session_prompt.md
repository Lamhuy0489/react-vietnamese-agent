# Prompt cho phiên sau

Cập nhật: 2026-11-07 22:30. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (08/11 14:50): Study 2. Vòng chỉnh 3 (SAN, cuối) xong: không cấu hình nào đạt luật khai báo, giữ D2+P2
(Bảng 2.5, decision log 08/11 14:00). WP8 lần 1 (fixture owner/Minh `data/adversarial/adaptive_v3/adaptive_dev_attack.jsonl`)
xong: bộ thích nghi yếu hơn bộ tĩnh ở A0 (4/6/6 so với 29/12/22), D2+P2 lọt 0/1/0 (Bảng 2.6). Không notebook nào cần giữ.

Việc của phiên này:
1. Hỏi owner duyệt final_config_v3. (a) D2+P2: ghi decision log, ghim manifest, chạy Test v3 một lần (3 backbone Tầng 1;
   hỏi có thêm Tầng 2), bootstrap theo family + McNemar; sau khi thấy số Test không đổi gì. (b) Mở vòng Dev mới với model
   lọc cố định: phải khai báo trước trong decision log.
2. Nếu owner/Minh đưa fixture WP8 vòng 2: kiểm hash, dry run, `build/kaggle/wp8_chain.sh` (hoặc `wp8_launch.sh` nếu cần notebook),
   `scripts/wp8_summary_v1.py`, cập nhật Bảng 2.6.
3. Treo: A6 (giải thích hay chạy mốc Dev); dọn ổ đĩa (cần owner duyệt, chưa xoá gì).

GPU: lamhuy8904 (kaggle.json), oanhlam123456 (kaggle6.json), buiquocviet (kaggle3.json), nomtle, dovuong05; mỗi tài khoản 2 GPU.
Claude không viết, đọc hay giao việc viết văn bản/prompt tấn công hay nội dung Test; chỉ hạ tầng và số đếm.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
