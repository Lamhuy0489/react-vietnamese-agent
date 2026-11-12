# Prompt cho phiên sau

Cập nhật: 2026-11-12. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): máy hỏng pin, chạy thẳng từ sạc 85 W. Không mở Zalo/app Electron/app nặng. Mỗi lúc một tiến trình nặng,
nice -n 10. Không kill hay khởi động lại OmniRoute. Lệnh dài: blocking hoặc run_in_background, không poll.

Trạng thái (12/11): thí nghiệm đã đóng. Bài báo ICCIES 2027 (hạn nộp 15/11/2026, Springer LNCS 12–15 trang, CMT).
Project LaTeX: docs/paper/iccies2027/latex/ (đọc docs/paper/iccies2027/README.md trước: cấu trúc, bảng đổi tên, checklist LNCS).
- sections/ là bản TIẾNG VIỆT để owner đọc; ICCIES cấm văn bản do AI sinh nên bản nộp tiếng Anh do owner tự viết.
  Claude làm: số liệu (chỉ từ facts.md), bảng, hình (images/src/*.py, --lang en ra images/en/), trích dẫn, định dạng, nhận xét.
- Tiêu đề owner chọn: "Beyond Model Compliance: A Layered Defence Against Indirect Prompt Injection in Vietnamese Tool-Using Agents".
- Tên trong bài là macro ở main.tex: BrokerGuard (=D3DEST), Rules (=D2), Rules+Sandwich (=D2+P2), NoDef (=A0), ER/CR/SL/AL/PT/US
  (=M1–M6), Test-I/Test-II (=Test v3/Test-3).
Việc của phiên này:
1. Hỏi owner số trang trên Overleaf; nếu > 15: bỏ Bảng 2 (ablation) hoặc gộp Bảng 4 với 5.
2. Owner quyết: tên phương pháp, công bố dữ liệu, tác giả/đơn vị. Đối chiếu Holm 1979 và model card Prompt Guard 2 (refs.bib UNVERIFIED).
3. Khi owner viết bản tiếng Anh: chuyển babel sang english, dùng hình images/en/, soát số với facts.md, nhận xét văn phong.
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
