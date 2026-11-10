# Prompt cho phiên sau

Cập nhật: 2026-11-10 23:05. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): máy hỏng pin hẳn, chạy thẳng từ sạc 85 W. Tuyệt đối không mở Zalo, app Electron hay app nặng trên Mac vì sẽ kích CPU Turbo Boost gây sập nguồn tức thì (-128). Mỗi lúc chỉ MỘT tiến trình nặng, nice -n 10, không dùng & để chạy nhiều lượt. Không kill hay khởi động lại OmniRoute.
Lệnh dài: chạy blocking hoặc run_in_background, không poll. Decision log 10/11 20:00.

Trạng thái (10/11 22:05): Test-3 xong (T1–T3 đạt, Bảng 2.10); Gemini Dev xong (Bảng 2.11); Llama 2048 token xong.
AgentDojo Gemini không phòng thủ XONG cả 8 lượt (10/11 21:53): Banking EN 93/144, 4/144; VI 99/144, 0/144; Slack EN 62/105, 1/105;
VI 59/105, 0/105. Transcript đã soát, Bảng 2.3b, Bảng 11 và facts.md đã điền (decision log 10/11 22:00). Không còn lượt nào đang chạy.
Việc của phiên này:
1. Thí nghiệm đã đóng: owner quyết 10/11 23:00 không chạy 8 lượt AgentDojo có phòng thủ trên Gemini (996 cặp); chỉ ghi hạn chế.
   Không chạy thêm lượt nào nếu owner không yêu cầu. PDF tài liệu tham khảo: docs/paper/iccies2027/refs/ (bảng ở refs/README.md).
2. Bài báo ICCIES 2027 (Springer CCIS, 12–15 trang, tiếng Anh, hạn nộp 15/11/2026, CMT): viết tiếp
   trong docs/paper/iccies2027/ (đọc README.md trước; số liệu chỉ lấy từ facts.md; bản thảo từng mục ở sections/). Đã có: Phần 1, Mục 2 threat model + M1–M6,
   Mục 3 D3, Bảng 1–11. Mục 4 (bản đầy đủ 10/11). Còn: prose Mục 5 kết quả (sửa chú thích Bảng 9: T2 là kiểm định z), Mục 6 thảo luận và hạn chế,
   Mục 7 kết luận, Hình 1 kiến trúc, tài liệu tham khảo (phải đối chiếu từng mục, chưa kiểm), chuyển sang template Springer.
   Số nào thiếu trong facts.md thì lấy từ docs/research/study2_thesis_tables.md rồi bổ sung vào facts.md; không ghi "utility trên 90%" (thực tế 51,0% so với A0 54,5%).
   Owner cần quyết: tiêu đề, có công bố dữ liệu không, tác giả và đơn vị.
3. Sau bài báo: chương kết quả Study 2 của luận văn theo dàn ý cuối study2_thesis_tables.md.

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
