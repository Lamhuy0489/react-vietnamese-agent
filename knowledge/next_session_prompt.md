# Prompt cho phiên sau

Cập nhật: 2026-11-19 tối. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy (owner dùng Overleaf), không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong,
không có notebook Kaggle nào chạy. Nếu phải chạy lại Kaggle: tắt IPv6 và bật `caffeinate -dimsu` trước.

Trạng thái (19/11 tối): BÀI v3 ĐÃ VIẾT XONG CẢ HAI BẢN ở docs/paper/brokerguard_v3/ (đọc README.md của thư mục trước:
nguồn số, bảng đổi tên log -> bài, quy tắc văn phong, việc owner cần làm). latex/ = tiếng Việt, latex_en/ = tiếng Anh
(cùng tên file, nhãn, bảng, hình, số; 10 mục, 6 bảng, 3 hình TikZ/pgfplots, 25 tài liệu), khoảng 20 trang LNCS, chưa
biên dịch. Tên trong bài: BrokerGuard = v3 (V3P2),
BG-Base = v1 (D2P2), Test-III = Test-4, Dev = Dev v4.1.

Việc của phiên này:
1. Hỏi owner đã biên dịch trên Overleaf chưa và có lỗi gì. Sửa lỗi biên dịch trước (owner dán log hoặc ảnh PDF vào root;
   PDF thì đọc bằng PyMuPDF ở dpi thấp, không render lại trên máy).
2. Sửa nội dung theo góp ý của owner. Văn phong học thuật, khách quan, không giống AI viết: không "chúng tôi/ta", không
   chấm phẩy trong lời văn, không gạch dài, tránh liệt kê máy móc. Số chỉ lấy từ docs/paper/iccies2027/facts.md; số mới
   thì ghi facts.md trước rồi mới đưa vào bài. Mã cơ chế chỉ trong bảng/hình; không nêu mã họ Test.
3. Mọi sửa nội dung phải làm ở cả latex/ và latex_en/ (số kiểu Việt và kiểu Anh). Nếu nơi nộp cấm văn bản do AI sinh,
   owner tự viết lại lời văn tiếng Anh.
4. Owner còn phải chốt: nơi nộp và template, tiêu đề, tác giả, tên phương pháp mới (nếu đổi thì sửa macro ở main.tex).

Không chạy thêm thực nghiệm hay sửa v3 theo số Test-4. Claude không viết, đọc hay giao việc viết văn bản/prompt tấn công
hay nội dung Test; chỉ hạ tầng, số đếm và biên soạn.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
