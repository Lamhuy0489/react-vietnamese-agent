# Prompt cho phiên sau

Cập nhật: 2026-11-18 (tối). Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy (owner dùng Overleaf), không tự khởi động lại OmniRoute. IPv6 Wi-Fi đang TẮT
(tránh địa chỉ trycloudflare chập chờn); bật lại khi không chạy Kaggle: `networksetup -setv6automatic Wi-Fi`.

Trạng thái (18/11 22:40): Test-4 xong (H1 không đạt do hiệu ứng sàn; decision log 18:40; số trong facts.md mục "Bài v3").
Đang chạy (handoff "Đang làm" có lệnh resume): (1) cột Gemini trên Test-4; (2) BrokerGuard v3 trên AgentDojo (Llama,
EN/VI × Banking/Slack, 4 notebook); (3) vòng thích nghi nhắm v3, 42 ca Dev-val do owner/Minh soạn (sha b348dcf8…),
3 model × A0/v1/v3 (qwen/gemma trên tài khoản mới tngdngpham = kaggle9.json; llama chờ slot lehung040324). Đã khai báo trước (decision log 19:30, 20:20, 20:55). Đừng suy notebook còn sống từ file
cũ: `build/kaggle/quota_all.sh` và `kaggle kernels status`.

Việc của phiên này:
1. Kiểm kê kết quả trên đĩa của ba việc trên; việc nào dở thì resume theo handoff. Đủ thì tổng hợp (chỉ số đếm) và ghi
   decision log + facts.md: Gemini là cột riêng, không kiểm định; AgentDojo v3 so với v1 (C10), repeat_user_prompt, không
   phòng thủ; thích nghi nhắm v3 so với bản canonical cùng họ, báo riêng.
2. Viết bài (một bài duy nhất, ICCIES chưa nộp; yêu cầu của thầy ở `Review Huy.docx`): đóng góp là cơ chế v3 + mô hình hình
   thức; v1 là biến thể luật chuỗi; H1 báo trung thực. Số chỉ lấy từ facts.md. Văn phong khách quan, không "chúng tôi".
3. Mẹo quota (owner): còn khoảng 1 h thì dừng và đẩy lại, mỗi tài khoản 2 notebook; được xóa notebook suy luận nhưng
   `kernels delete` xóa mọi phiên bản của slug, chỉ xóa khi không phiên bản nào khác đang chạy.
4. Không chỉnh v3 hay chạy lại theo số Test-4 hoặc các vòng phụ (chỉ chạy lại khi lỗi hạ tầng).

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
