# Prompt cho phiên sau

Cập nhật: 2026-11-10 20:00. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): máy hỏng pin hẳn, chạy thẳng từ sạc 85 W. Mỗi lúc chỉ MỘT tiến trình nặng, nice -n 10, không dùng &
để chạy nhiều lượt, không chạy lại gemini3_agentdojo_chain.sh (8 lượt song song). Không kill hay khởi động lại OmniRoute.
Lệnh dài: chạy blocking hoặc run_in_background, không poll. Decision log 10/11 20:00.

Trạng thái (10/11 20:00): Test-3 xong (T1–T3 đạt, Bảng 2.10); Gemini Dev xong (Bảng 2.11); Llama 2048 token xong.
AgentDojo Gemini không phòng thủ: 4 utility + VI Slack + VI Banking + EN Slack xong (EN Slack 62/105, 1/105);
EN Banking đang chạy tuần tự (120/144 lúc 19:45) bằng build/gemini/ad_seq_finish.sh, proxy 8445 nhịp 4 s, chậm do pool
hạ nhiệt 15 phút. Bảng 2.3b còn thiếu ô Banking EN.

Việc của phiên này:
1. Kiểm EN Banking: pgrep -fl run_agentdojo_api_v1.py; summary.json ở
   results/rebuild_b/agentdojo_en_banking_important_instructions_none_gemini3_flash_raw. Runner chết mà chưa có summary và
   proxy 8445 còn nghe: nice -n 10 bash build/gemini/ad_seq_finish.sh (resume). Lệnh chi tiết ở handoff "Đang làm".
2. Khi xong: soát transcript (kết thúc bằng assistant, không dấu lỗi API), điền Bảng 2.3b và Bảng 11 của bản nháp bài báo,
   ghi decision log.
3. Hỏi owner: có chạy 8 lượt AgentDojo có phòng thủ dựng sẵn không (996 cặp, 16–33 giờ máy). Gemini là phần phụ; đề xuất bỏ
   và ghi hạn chế. Không tự chạy.
4. Bài báo ICCIES 2027 (Springer CCIS, 12–15 trang, tiếng Anh, hạn nộp 15/11/2026, CMT): viết tiếp
   trong docs/paper/iccies2027/ (đọc README.md trước; số liệu chỉ lấy từ facts.md; bản thảo từng mục ở sections/). Đã có: Phần 1, Mục 2 threat model + M1–M6,
   Mục 3 D3, Bảng 1–11. Còn: Mục 4 benchmark và giao thức (đang là dàn ý), prose Mục 5 kết quả, Mục 6 thảo luận và hạn chế,
   Mục 7 kết luận, Hình 1 kiến trúc, tài liệu tham khảo (phải đối chiếu từng mục, chưa kiểm), chuyển sang template Springer.
   Số nào thiếu trong facts.md thì lấy từ docs/research/study2_thesis_tables.md rồi bổ sung vào facts.md; không ghi "utility trên 90%" (thực tế 51,0% so với A0 54,5%).
   Owner cần quyết: tiêu đề, có công bố dữ liệu không, tác giả và đơn vị.
5. Sau bài báo: chương kết quả Study 2 của luận văn theo dàn ý cuối study2_thesis_tables.md.

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
