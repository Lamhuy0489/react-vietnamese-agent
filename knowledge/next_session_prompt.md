# Prompt cho phiên sau

Cập nhật: 2026-11-18 (tối). Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy (owner dùng Overleaf), không tự khởi động lại OmniRoute. IPv6 Wi-Fi đang TẮT
(tránh địa chỉ trycloudflare chập chờn); bật lại khi không chạy Kaggle: `networksetup -setv6automatic Wi-Fi`.

Trạng thái (19/11 00:30): Test-4 xong (H1 không đạt do hiệu ứng sàn; decision log 18/11 18:40). Gemini Test-4 xong (cột
tham khảo, facts.md). Đang chạy, đọc handoff "Đang làm" mục 2026-11-19 00:30 để có lệnh resume:
(1) AgentDojo v3 (3 bộ có tấn công); (2) thích nghi nhắm v3: Qwen/Gemma xong, Llama chờ slot lehung040324;
(3) baseline bổ sung R1, D2, P1, MEL, G1 trên Test-4 rồi Dev v4.1 × 3 mô hình (`supp_launch.sh`; decision log 19/11 00:25);
G1 cần Prompt Guard local cổng 8765. Đừng suy notebook còn sống từ file cũ: `build/kaggle/quota_all.sh`, `kaggle kernels status`.

Việc của phiên này:
1. Kiểm kê kết quả trên đĩa; việc nào dở thì resume theo handoff (notebook chết, hết quota: đẩy lại; tài khoản kaggle9.json
   tngdngpham còn nhiều giờ; 7 tài khoản cũ đặt lại 21/11 07:00 giờ VN). Mục tiêu owner: Test-4 bổ sung xong trong 19/11.
2. Tổng hợp (chỉ số đếm) vào decision log + facts.md: AgentDojo v3 so với v1 (C10); thích nghi nhắm v3 so với canonical cùng
   họ, báo riêng; baseline bổ sung là mô tả, ngoài H1–H4, McNemar họ gộp so với v3 ghi là khám phá. Dùng lại hàm của
   `scripts/test4_analysis_v1.py`, như `scripts/test4_gemini_ref_v1.py`.
3. Viết bài (một bài duy nhất; yêu cầu của thầy ở `Review Huy.docx`): đóng góp là cơ chế v3 + mô hình hình thức; v1 là
   biến thể luật chuỗi; H1 báo trung thực; bảng dòng phát triển R1 → D2 → D2P2 → v3 trên cùng Test-4. Số chỉ lấy từ facts.md.
   Văn phong khách quan, không "chúng tôi". Còn chờ owner trả lời: thư mục bài, ngôn ngữ nháp, tên phương pháp.
4. Mẹo quota: còn khoảng 1 h thì dừng và đẩy lại, mỗi tài khoản 2 notebook; `kernels delete` xóa mọi phiên bản của slug.
5. Không chỉnh v3 hay chạy lại theo số Test-4 (chỉ chạy lại khi lỗi hạ tầng). Lỗi mô hình (OUTPUT_TRUNCATED 512 token,
   Gemini OUTPUT_INVALID) không chạy lại; nêu trong hạn chế, có thể thêm phân tích độ nhạy bỏ ca lỗi.

Claude không viết, đọc hay giao việc viết văn bản/prompt tấn công hay nội dung Test; chỉ hạ tầng, số đếm và biên soạn.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
