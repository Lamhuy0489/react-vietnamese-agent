# Prompt cho phiên sau

Cập nhật: 2026-11-14. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): máy hỏng pin, chạy thẳng từ sạc 85 W. Không mở app nặng. Mỗi lúc một tiến trình nặng, nice -n 10.
Không kill hay khởi động lại OmniRoute. KHÔNG render hình hay biên dịch PDF trên máy: owner biên dịch trên Overleaf.
Xem PDF owner thả ở root: PyMuPDF (python3 hệ thống) dpi thấp.

Trạng thái (15/11): thí nghiệm đã đóng. Bài ICCIES 2027 (hạn 15/11, LNCS 12–15 trang). Tiêu đề: "BrokerGuard: A Layered
Defence with Tool-Broker Enforcement Against Indirect Prompt Injection in Vietnamese LLM Agents".
- `docs/paper/iccies2027/latex_en/` = bản nộp tiếng Anh (Claude dịch theo yêu cầu owner 14/11; owner đã được nhắc quy định
  ICCIES về văn bản AI). `latex/` = bản tiếng Việt cùng nội dung. Sửa nội dung thì sửa CẢ HAI.
- Số liệu chỉ từ facts.md. 19 tài liệu (có FIDES, ClawGuard), tài liệu tham khảo dạng gọn (venue viết tắt, et al., doi:).
- Quy ước: không ngôi thứ nhất; không commit/Git/proxy/JSON; không link repo (chỉ "publicly released"); mã cơ chế chỉ ở
  Bảng 1/Hình 2/dòng H3; "plain/authorised benign" (macro \bPlain, \bAuth); nhãn hình ngắn; câu ngắn, không chấm phẩy.
- KHÔNG dùng regex đổi dấu phẩy thập phân trên file hình TikZ/pgfplots (đã phá tọa độ một lần).
Việc của phiên này (handoff "Đang làm" 15/11 00:30):
1. Hỏi owner PDF bản EN: ≤ 15 trang? Hình 1 không chồng chữ? Bảng 4 không tràn? Nếu thừa: bỏ nửa dưới Bảng 4 hoặc gộp
   đoạn "Language" (Mục 7) vào 6.2, sửa cả hai bản.
2. Owner điền tác giả/đơn vị/e-mail, xóa \todo trước khi nộp; đối chiếu tác giả ClawGuard (arXiv 2604.11790).
3. Sau khi nộp: chương kết quả Study 2 của luận văn (dàn ý cuối docs/research/study2_thesis_tables.md).

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
