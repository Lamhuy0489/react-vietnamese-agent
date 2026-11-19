# Prompt cho phiên sau

Cập nhật: 2026-11-20. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy (owner dùng Overleaf; đọc PDF owner tải về bằng PyMuPDF của python3 hệ thống ở
dpi thấp thì được), không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong, không có notebook Kaggle nào chạy.

Trạng thái (20/11): BÀI v3 ĐÃ RÚT CÒN TỐI ĐA 15 TRANG ở docs/paper/brokerguard_v3/ (latex/ = tiếng Việt, latex_en/ =
tiếng Anh, cùng nội dung, số, nhãn). Đọc README.md của thư mục trước: mục "Bản 15 trang: đã cắt gì", "Ước lượng trang",
"Việc owner cần làm", bảng đổi tên log -> bài, quy tắc văn phong. Hiện có 5 bảng, Hình 1 (kiến trúc), Hình Pareto tùy
chọn (\paretotrue ở main.tex, mặc định tắt), 19 tài liệu. Ước lượng chưa biên dịch: bản Việt ~14,1 trang, bản Anh ~14,4
trang; bật Pareto thêm ~0,37 trang. Bản 23 trang đã biên dịch: pdf/agent_injection_vn.pdf; bản dài: commit 6814b3a.

Việc của phiên này:
1. Hỏi owner số trang thật sau khi biên dịch cả hai bản trên Overleaf và lỗi nếu có (PDF tải về
   docs/paper/brokerguard_v3/pdf/). Sửa lỗi biên dịch trước. Quá 15 trang thì cắt theo danh sách ứng viên trong README
   (bản Anh dài hơn bản Việt nên là bản quyết định). Dưới ~14,6 trang thì hỏi owner có bật Hình Pareto không.
2. Sửa nội dung theo góp ý của owner. Văn phong học thuật, khách quan, không giống AI viết: không "chúng tôi/ta"/"we",
   không chấm phẩy trong lời văn, không gạch dài, tránh liệt kê máy móc. Số chỉ lấy từ docs/paper/iccies2027/facts.md;
   số mới thì ghi facts.md trước. Mã cơ chế chỉ trong bảng; không nêu mã họ Test. Thêm gì thì bớt tương ứng để giữ 15 trang.
3. Mọi sửa nội dung làm ở cả latex/ và latex_en/ (số kiểu Việt và kiểu Anh). Nếu nơi nộp cấm văn bản do AI sinh, owner
   tự viết lại lời văn tiếng Anh.
4. Owner còn phải chốt: nơi nộp và template, tiêu đề, tác giả, tên phương pháp (nếu đổi thì sửa macro ở main.tex).

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
