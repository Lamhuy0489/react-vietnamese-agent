# Prompt cho phiên sau

Cập nhật: 2026-11-19 12:15. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy (owner dùng Overleaf), không tự khởi động lại OmniRoute. Nếu IPv6 Wi-Fi còn tắt
và không chạy Kaggle: `networksetup -setv6automatic Wi-Fi`. Prompt Guard local (127.0.0.1:8765) chỉ cần khi chạy G1.

Trạng thái (19/11 12:15): MỌI THỰC NGHIỆM XONG. Test-4 (H1 không đạt do hiệu ứng sàn; decision log 18/11 18:40), Gemini
Test-4, Test-4 và Dev v4.1 bổ sung R1/D2/P1/MEL/G1, thích nghi nhắm v3, AgentDojo v3: số đầy đủ trong facts.md. Không còn
notebook nào chạy (kiểm bằng `build/kaggle/quota_all.sh` nếu cần).

Việc của phiên này:
1. Viết bài (một bài duy nhất; yêu cầu của thầy ở `Review Huy.docx`): đóng góp là cơ chế v3 + mô hình hình thức; v1 là
   biến thể luật chuỗi; H1 báo trung thực; bảng dòng phát triển R1 → D2 → D2P2 → v3 trên cùng Test-4 (và Dev v4.1 làm
   bảng phụ). Số chỉ lấy từ facts.md. Văn phong khách quan, không "chúng tôi". Hỏi owner trước: thư mục bài, ngôn ngữ
   nháp, tên phương pháp.
2. Tùy chọn (owner chưa trả lời): phân tích độ nhạy bỏ ca lỗi mô hình (OUTPUT_TRUNCATED 512 token, Gemini OUTPUT_INVALID);
   không chạy lại các ca đó.
3. Không chỉnh v3 hay chạy lại theo số Test-4. Quota: phmkimphng ~13 h, tngdngpham ~13,5 h (đặt lại 21/11); mẹo: còn ~1 h
   thì dừng và đẩy lại, mỗi tài khoản 2 notebook.

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
