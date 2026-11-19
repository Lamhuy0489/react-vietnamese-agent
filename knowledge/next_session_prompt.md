# Prompt cho phiên sau

Cập nhật: 2026-11-20. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy (owner dùng Overleaf; đọc PDF owner tải về bằng PyMuPDF của python3 hệ thống ở
dpi thấp thì được), không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong, không có notebook Kaggle nào chạy.

Trạng thái (20/11, sau): BÀI v3 rút còn tối đa 15 trang ở docs/paper/brokerguard_v3/ (latex/ = tiếng Việt, latex_en/ =
tiếng Anh). Đọc README.md của thư mục trước, nhất là mục "Góp ý owner lần 1" và dòng "Cỡ chữ bảng" (LNCS in bảng ở
9 pt; tabular* rộng quá khổ thì tràn mà adjustbox không thu). BẢN VIỆT đã sửa theo góp ý lần 1 (Bảng 1 hết tràn, Bảng
3, 4 tách cột Q, G, L, tóm tắt/Mục 1, 7, 8, 9 diễn đạt lại kết quả so với luật so khớp chuỗi, bật Hình Pareto, ước
lượng ~14,85 trang). BẢN ANH CHƯA sửa theo lần này (Pareto đang tắt, ước lượng ~14,6 trang).

Việc của phiên này:
1. Hỏi owner kết quả biên dịch lại bản Việt (số trang, bảng còn tràn không). Vượt 15 trang thì \paretofalse hoặc cắt.
2. Làm bản Anh y hệt bản Việt theo danh sách trong README ("Góp ý owner lần 1"): Bảng 1 tabularx, Bảng 3, 4 tách cột,
   tóm tắt và Mục 1, 7, 8, 9 diễn đạt lại (không nói quá: BrokerGuard chặn 4 trong 6 họ mà luật chuỗi để lọt), rồi viết
   gọn thêm ~0,25 trang và bật Pareto. Đo bề rộng bảng ở 9 pt trước khi dùng tabular*.
3. Sửa nội dung theo góp ý tiếp của owner, ở cả hai bản. Văn phong học thuật, khách quan, không "chúng tôi/ta"/"we",
   không chấm phẩy trong lời văn, không gạch dài. Số chỉ từ docs/paper/iccies2027/facts.md. Thêm gì thì bớt tương ứng.
4. Owner còn phải chốt: nơi nộp và template, tiêu đề, tác giả, tên phương pháp.

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
