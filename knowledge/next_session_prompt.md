# Prompt cho phiên sau

Cập nhật: 2026-11-09 14:15. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái (09/11 14:15): Study 2. Test v3 Tầng 1 XONG (Bảng 2.7, 2.8). Owner duyệt làm D3 trên Dev:
branch study2/d3-dev (commit ee0fc1c), thiết kế + tiêu chí ghi trước ở decision log 09/11 13:00. final_config_v3
giữ ở tag final-config-v3 (trên branch D3, final_config_v3.verify báo khác là đúng; Test v3/Tầng 2 chạy từ tag).
3 notebook D3 Dev đang/đã chạy {D3, D3DEST, D3P2V1, D3FBV1} × 560: Gemma dovuong05, Llama 16k lamhuy8904,
Qwen3.5 meanalways (handoff "Đang làm" có lệnh resume; log build/kaggle/d3_logs/).

Việc của phiên này:
1. Kiểm kaggle kernels status; ô nào chưa đủ 560 thì bật lại bằng build/kaggle/d3_supervise.sh (đổi tài khoản nếu hết quota).
2. Khi đủ: evaluate_v3_v1.py từng ô, so với D2P2 Dev theo tiêu chí decision log (có hại ≤ D2P2, utility > D2P2),
   ablation từng thành phần; ghi Bảng 2.9 và decision log; nếu đạt thì đóng băng final_config_v4.
3. Hỏi owner/Minh có soạn Test-3 (niêm phong) không; không có thì D3 chỉ báo cáo là thử nghiệm Dev.
4. Viết chương kết quả Study 2 từ Bảng 2.1–2.8.

GPU: nomtle, huylmhuhu, buiquocviet, oanhlam hết quota tuần 09/11. Mỗi tài khoản 2 phiên GPU. Owner cho đổi tài khoản.
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
