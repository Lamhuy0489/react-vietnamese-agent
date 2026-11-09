# Prompt cho phiên sau

Cập nhật: 2026-11-09 22:20. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (09/11 22:20): Study 2. D3 Dev xong, chọn D3DEST (decision log 21:20). Test-3 niêm phong, final_config_v4
(sha256 59f32eea…) owner duyệt 21:40; Test-3 ĐANG CHẠY một lần từ worktree ../wt-test3 (branch study2/test3-seal):
9 ô {A0, D2P2, D3DEST} × {gemma4_12b, llama31_8b, qwen35_9b}, notebook lamhuy8904 (Gemma, Llama) + meanalways (Qwen).
Keep-alive giữ 3 notebook tới ~09:07 10/11 (giới hạn 12 h); lamhuy8904 hết quota sau phiên này (meanalways còn nhiều).
Dự kiến 9 ô xong ~04–06h 10/11. Gemini 3 Flash Dev chạy lại với --extract-json trên máy owner (OmniRoute, nhịp 2 s).
Lệnh resume ở handoff "Đang làm".

Việc của phiên này:
1. Đếm result.json ở results/rebuild_b/v3_test3_<CFG>_<K> và kaggle kernels status; ô nào chưa đủ 560 thì chạy lại
   build/kaggle/t3_chain.sh K (resume). Notebook chết: HF_TOKEN="$(cat ~/.hf_token_r5)" build/kaggle/t3_serve.sh
   OWNER CRED SERVE_KEY K trên tài khoản còn quota (meanalways kaggle2.json; ít quota thì bật 2 phiên cùng lúc), rồi t3_chain.sh K.
2. Khi đủ 9 ô: evaluate_v3_v1.py, tính T1–T3 đúng như freeze_final_config_v4.py (Holm); bảng + decision log; không chỉnh gì theo Test.
3. Merge study2/test3-seal về branch chính; cập nhật knowledge.
4. Gemini Dev: khi xong 4 cấu hình thì evaluate và so với kết quả _nojsonfix.
5. Viết chương kết quả Study 2.

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
