# Prompt cho phiên sau

Cập nhật: 2026-11-09 10:00. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (09/11 10:00): Study 2. Test v3 Tầng 1 XONG một lần dưới final_config_v3 (D2+P2): Bảng 2.7 trong
docs/research/study2_thesis_tables.md, decision log 09/11 10:00, results/rebuild_b/v3_test_hypotheses.json.
H1, H3, H6 bác H0; H2 (D2 plain không kém quá 5 điểm) chưa chứng minh; H4, H5 không khác. WP8 vòng 3 xong (Bảng 2.6b).
Không notebook nào cần giữ.

Việc của phiên này:
1. Viết chương kết quả Study 2 (thesis/) từ Bảng 2.1–2.7, nêu rõ Dev và Test, hạn chế (WP8 do người soạn, chỉ Dev).
2. Nếu còn GPU trước 2026-12-14: Test Tầng 2 + SecAlign theo test_matrix của manifest (test_launch.sh, test_supervise.sh).
3. Hỏi owner: Gemini (billing có trần hay bỏ); commit hay gitignore data/adversarial/adaptive_v3/ và
   v3_authoring/adaptive_attacks.json.
Không đổi gì trong src/react_agent hay configs nếu còn chạy Test (manifest verify).

GPU: nomtle (kaggle5), dovuong05 (kaggle4), huylmhuhu (kaggle1), lamhuy8904 (kaggle.json), meanalways (kaggle2); buiquocviet
và oanhlam hết quota tuần 09/11. Mỗi tài khoản 2 phiên GPU. Owner cho đổi tài khoản khi hết quota.
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
