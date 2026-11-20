# Prompt cho phiên sau

Cập nhật: 2026-11-20. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy (owner dùng Overleaf; đọc PDF owner tải về bằng PyMuPDF của python3 hệ thống ở
dpi thấp thì được), không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong, không có notebook Kaggle nào chạy.

Trạng thái (20/11, đêm): BÀI v3 ở docs/paper/brokerguard_v3/ (latex/ = tiếng Việt, latex_en/ = tiếng Anh), đã merge vào
main. Bản Anh: phông Times (newtx + microtype) như bài tham khảo trong pdf/, Hình 2 bật với [H], ít ký hiệu trong lời
văn, thêm lại nội dung hỗ trợ (phát triển và đóng băng, loại hại, biến thể ngôn ngữ, phát lại Dev-val theo thành phần,
C1 chấm riêng, lộ ở câu trả lời cuối), Disclosure of Interests; ước lượng ~14,7 trang. Tác giả: Quang Huy Lam, Quang
Minh Nguyen (Khoa CNTT, Trường ĐH Xây dựng Hà Nội), đã điền ở cả hai bản. Đọc README.md của thư mục (mục "Lượt 3",
"Lượt 3c", "Lượt 4").

Việc của phiên này:
1. Hỏi owner số trang thật của bản Anh và vị trí Hình 2. Quá 15 trang thì cắt câu trùng với bảng hoặc \paretofalse.
2. Đồng bộ bản Việt với bản Anh: đổi phông Times có T5 (thử \usepackage{tgtermes} với newtxmath trên Overleaf), áp
   các thay đổi lượt 3b, 3c, 4 và các sửa nhỏ lượt 3, giữ số liệu khớp, ≤ 15 trang.
3. Owner còn phải chốt: nơi nộp, quy định về văn bản có AI hỗ trợ.

Văn phong học thuật, khách quan, dễ hiểu, không "chúng tôi/ta"/"we", không chấm phẩy trong lời văn, không gạch dài, ít
ký hiệu ngoài Mục 4–5. Số chỉ lấy từ docs/paper/iccies2027/facts.md. Commit và PR không ghi Claude là đồng tác giả.
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
