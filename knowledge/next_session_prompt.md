# Prompt cho phiên sau

Cập nhật: 2026-11-14. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): máy hỏng pin, chạy thẳng từ sạc 85 W. Không mở Zalo/app Electron/app nặng. Mỗi lúc một tiến trình
nặng, nice -n 10. Không kill hay khởi động lại OmniRoute. KHÔNG render hình hay biên dịch PDF trên máy: owner biên dịch
trên Overleaf; hình mới vẽ bằng TikZ/pgfplots trong file .tex.

Trạng thái (14/11): thí nghiệm đã đóng, kể cả C10 (BrokerGuard trên AgentDojo, xong 14/11 03:05). Bài báo ICCIES 2027 (hạn 15/11/2026, Springer LNCS 12–15 trang, CMT).
Đọc docs/paper/iccies2027/README.md (mục "Luận điểm" đổi 13/11) và facts.md (mục "Bổ sung sau phản biện").
- 13/11 owner quyết bỏ BG-v2 (D3DEST): bài chỉ còn BrokerGuard = D2+P2 (macro \cRulesS = \ours), BG-Rules = D2 để tách lớp.
  Test-I: H1–H6 đăng ký trước; Test-II: BrokerGuard vs NoDef là phân tích lặp lại không đăng ký trước. Suy luận mức family.
- Phản biện ở root `phan bien.md` (không commit). Đã xử lý bằng chữ và tính offline: A1–A5, B1–B3, C1–C5, C9, C11, D5.
  Chưa làm (ghi ở Hạn chế): C8 tấn công hộp trắng, oracle-C, ablation phản hồi, độ trễ.
- C10 xong: facts.md mục C10; Bảng 6 thêm Sandwich/BrokerGuard; tóm tắt, Mục 5–8 đã cập nhật 14/11 (chưa biên dịch).
  Lưu ý: 2/6 ca EN Slack là lời gọi đã bị chặn nhưng hàm chấm AgentDojo vẫn tính; utility Slack giảm do R-Dest.
- sections/ là bản TIẾNG VIỆT để owner đọc; bản nộp tiếng Anh owner tự viết (ICCIES cấm văn bản AI). Claude làm số liệu
  (chỉ từ facts.md), bảng, hình, trích dẫn, định dạng, nhận xét bản owner viết.
- Văn phong owner muốn: câu ngắn, không chấm phẩy trong lời văn, không gạch dài; link trích dẫn xanh bấm được.
- Xem PDF owner tải: đặt ở root repo, xuất ảnh trang bằng PyMuPDF (fitz) dpi thấp; Read PDF không chạy (thiếu poppler).
Việc của phiên này:
1. Hỏi owner kết quả biên dịch (số trang sau khi thêm C10, lỗi TikZ ở Hình 1 `images/fig1_pipeline.tex`, Bảng 6 tràn).
2. Owner duyệt phần C10 trong bài (Bảng 6, Mục 6 đoạn cuối, Mục 7, tóm tắt thêm một câu: kiểm độ dài ≤ 250 từ bản EN).
3. Owner quyết: công bố dữ liệu; tác giả/đơn vị. Đối chiếu Holm 1979 (refs.bib).
4. Khi owner viết bản tiếng Anh: đổi babel sang english, bỏ T5, đổi nhãn Hình 1 theo comment đầu fig1_pipeline.tex, dịch
   nhãn Hình 2, soát số với facts.md, tóm tắt ≤ 250 từ, nhận xét văn phong.
5. Sau bài báo: chương kết quả Study 2 của luận văn (vẫn giữ D3; dàn ý cuối docs/research/study2_thesis_tables.md).

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
