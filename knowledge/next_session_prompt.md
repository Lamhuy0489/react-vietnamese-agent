# Prompt cho phiên sau

Cập nhật: 2026-11-20. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy (owner dùng Overleaf; đọc PDF owner tải về bằng PyMuPDF của python3 hệ thống ở
dpi thấp thì được), không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong, không có notebook Kaggle nào chạy.

Trạng thái (20/11, khuya): BÀI v3 ở docs/paper/brokerguard_v3/ (latex/ = tiếng Việt, latex_en/ = tiếng Anh) đã qua ba
lượt góp ý. Lượt 3: bớt ký hiệu và ngoặc, Gemini chỉ là mô hình đóng của Google, chú thích ngắn, khối tác giả để trống
tự điền, câu mở và câu nối giữa các mục (tham khảo bài lượng tử trong pdf/). Bản Anh bật Hình 2 với [H] ngay sau đoạn
"Main results" (ước lượng ~14,8 trang). Bản Việt tắt Pareto (~14,7 trang) và còn vài sửa nhỏ chưa áp. Đọc README.md của
thư mục trước (mục "Lượt 3").

Việc của phiên này:
1. Hỏi owner số trang thật của bản Anh (đã đổi sang Times, thêm lại nội dung ở lượt 4) và vị trí Hình 2. Nếu Hình 2 để trống cuối trang: dời dòng
   \ifpareto\input{images/fig2_pareto}\fi trong sections/07_results.tex. Nếu quá 15 trang: cắt câu trùng với bảng.
2. Áp cho bản Việt các sửa nhỏ còn lại và lượt giảm ký hiệu 3c của bản Anh (README, mục "Lượt 3" và "Lượt 3c"),
   giữ số liệu khớp bản Anh.
3. Owner còn phải chốt: nơi nộp và template, ẩn danh hay không, tiêu đề, tác giả, quy định về văn bản có AI hỗ trợ.

Văn phong học thuật, khách quan, không "chúng tôi/ta"/"we", không chấm phẩy trong lời văn, không gạch dài. Số chỉ lấy
từ docs/paper/iccies2027/facts.md. Không chạy thêm thực nghiệm hay sửa v3 theo số Test-4. Claude không viết, đọc hay
giao việc viết văn bản/prompt tấn công hay nội dung Test; chỉ hạ tầng, số đếm và biên soạn.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
