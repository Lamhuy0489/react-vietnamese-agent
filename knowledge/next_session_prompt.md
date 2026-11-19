# Prompt cho phiên sau

Cập nhật: 2026-11-20. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy (owner dùng Overleaf; đọc PDF owner tải về bằng PyMuPDF của python3 hệ thống ở
dpi thấp thì được), không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong, không có notebook Kaggle nào chạy.

Trạng thái (20/11, tối): BÀI v3 ở docs/paper/brokerguard_v3/ (latex/ = tiếng Việt, latex_en/ = tiếng Anh) đã qua hai lượt
góp ý của owner: bảng tách cột, Bảng 1 hết tràn, H1 diễn đạt tích cực nhưng trung thực, soát văn phong, khối tác giả ẩn
danh. Bản Việt bật Hình Pareto (ước lượng ~14,8 trang), bản Anh tắt (~14,7 trang). Đọc README.md của thư mục trước (mục
"Lượt 2", dòng "Cỡ chữ bảng": LNCS in bảng ở 9 pt).

Việc của phiên này:
1. Hỏi owner số trang thật của cả hai bản sau khi biên dịch. Bản nào quá 15 trang: tắt Pareto hoặc cắt câu trùng với
   bảng (không cắt kết quả chính). Đo bề rộng bảng ở 9 pt trước khi đổi bảng.
2. Sửa nội dung theo góp ý tiếp của owner, ở cả hai bản, giữ số liệu khớp nhau. Văn phong học thuật, khách quan, không
   "chúng tôi/ta"/"we", không chấm phẩy trong lời văn, không gạch dài, tránh nối vế bằng "còn" lặp lại.
3. Owner còn phải chốt: nơi nộp và template, ẩn danh hay không, tiêu đề, tác giả, quy định về văn bản có AI hỗ trợ.

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
