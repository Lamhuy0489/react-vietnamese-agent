# Prompt cho phiên sau

Cập nhật: 2026-11-12 20:30. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): máy hỏng pin, chạy thẳng từ sạc 85 W. Không mở Zalo/app Electron/app nặng. Mỗi lúc một tiến trình
nặng, nice -n 10. Không kill hay khởi động lại OmniRoute. KHÔNG render hình hay biên dịch PDF trên máy: owner biên dịch
trên Overleaf; hình mới vẽ bằng TikZ/pgfplots trong file .tex.

Trạng thái (12/11 20:30): thí nghiệm đã đóng. Bài báo ICCIES 2027 (hạn 15/11/2026, Springer LNCS 12–15 trang, CMT).
Đọc docs/paper/iccies2027/README.md trước (cấu trúc, bảng đổi tên, checklist LNCS). Project: docs/paper/iccies2027/latex/.
- sections/ là bản TIẾNG VIỆT để owner đọc; bản nộp tiếng Anh owner tự viết (ICCIES cấm văn bản AI). Claude làm số liệu
  (chỉ từ facts.md), bảng, hình, trích dẫn, định dạng, nhận xét bản owner viết.
- Tiêu đề: "Beyond Model Compliance: A Layered Defence Against Indirect Prompt Injection in Vietnamese Tool-Using Agents".
- Tên (macro trong main.tex): BrokerGuard; BG-Rules=D2, BG-v1=D2+P2 (Test-I), BG-v2=D3DEST (Test-II); NoDef=A0;
  ER/CR/SL/AL/PT/US = M1–M6; Test-I/Test-II = Test v3/Test-3. Cả BG-v1 và BG-v2 là đóng góp; không viết "đầu tiên".
- Văn phong owner muốn: câu ngắn, không chấm phẩy trong lời văn, không gạch dài; link trích dẫn xanh bấm được.
- Xem PDF owner tải: đặt ở root repo, xuất ảnh trang bằng PyMuPDF (fitz) dpi thấp; Read PDF không chạy (thiếu poppler).
Việc của phiên này:
1. Hỏi owner kết quả biên dịch mới (số trang, bảng tràn, chỗ trắng); xem PDF nếu owner đặt vào repo.
2. Owner quyết: chạy Gemini cho 5 baseline Dev còn thiếu không (đề xuất chỉ Sandwich, cần owner bật OmniRoute + proxy 8445);
   công bố dữ liệu; tác giả/đơn vị. Đối chiếu Holm 1979 (refs.bib).
3. Khi owner viết bản tiếng Anh: đổi babel sang english, bỏ T5, dùng images/en/fig1_pipeline.pdf, dịch nhãn Hình 2 trong
   fig2_results.tex, soát số với facts.md, tóm tắt ≤ 250 từ, nhận xét văn phong.
4. Sau bài báo: chương kết quả Study 2 của luận văn (dàn ý cuối docs/research/study2_thesis_tables.md).

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
