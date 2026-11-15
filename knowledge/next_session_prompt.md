# Prompt cho phiên sau

Cập nhật: 2026-11-15. Mở `claude` hoặc Antigravity ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): máy hỏng pin, chạy thẳng từ sạc 85 W. Không mở app nặng. Mỗi lúc một tiến trình nặng, nice -n 10.
Không tự bật hay khởi động lại OmniRoute (owner bật). KHÔNG render hình hay biên dịch PDF trên máy: owner dùng Overleaf.

Trạng thái (15/11 15:30): hạn nộp ICCIES đã lùi. Owner quyết mở rộng bài theo `Review Huy.docx` (root, không commit):
BrokerGuard v3 = C1 chính sách ý định P(u) có cực tính (tất định), C2 nhãn độ nhạy theo giá trị, C3 toàn vẹn tham số;
mô hình hình thức s_t=(u,C_t,P_t,H_t) với ba thuộc tính; Test-4 niêm phong mới; đo token/thời gian và đường Pareto.
Thiết kế nháp: `docs/project/brokerguard_v3_extension_design.md` (decision log 2026-11-15 15:30). Bài hiện tại ở
`docs/paper/iccies2027/latex_en/` (EN) và `latex/` (VI), sửa cả hai; số liệu chỉ từ facts.md.

Việc của phiên này:
1. Owner đã duyệt (decision log 15:45): tạp chí Q4; cần xác nhận = từ chối; bộ trích P(u) tất định; Test-4 48 họ do
   owner+Minh soạn. Còn hỏi: tên phương pháp, hạn tạp chí, tiến độ soạn Test-4.
2. Việc Claude làm được ngay, không đợi Test-4: thêm log token và thời gian vào runner (file mới, có test); soạn mô hình
   hình thức và mệnh đề; kiểm CapLite là bài thật trước khi trích.
3. KHÔNG viết code v3 trước khi Test-4 được niêm phong (hash trong decision log). Không sửa v1, Test cũ, số liệu đã có.

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
