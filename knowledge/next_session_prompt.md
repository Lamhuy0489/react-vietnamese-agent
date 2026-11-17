# Prompt cho phiên sau

Cập nhật: 2026-11-17. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): pin hỏng VĨNH VIỄN, chạy thẳng từ sạc 85 W. Chạy nhẹ: mỗi lúc một việc, nice -n 10, không mở app
nặng, KHÔNG chạy pytest toàn bộ (~1 giờ) mà chỉ test module đã đụng + lân cận. Không tự bật hay khởi động lại OmniRoute.
KHÔNG render hình hay biên dịch PDF trên máy: owner dùng Overleaf. Khi có chuỗi Kaggle chạy: giữ một
`caffeinate -dimsu` độc lập (kiểm `pmset -g assertions`), không để máy ngủ hay tắt màn hình.

Trạng thái (17/11 11:45): BrokerGuard v3 cho tạp chí Q4. Dev v4.1 xong: mốc 12/12 và V3P2 ba mô hình (gây hại còn
1–3/840, chỉ M5; lộ câu cuối 0; utility giữ nguyên; chặn nhầm tăng) và ablation Dev-val (C2, C3 đạt; C1 không đạt), decision
log 2026-11-17 07:00, 08:30, 11:30, 11:45. Test-4 (seal `1f9b0070…`) niêm phong. Quota GPU hết đến 21/11 07:00 giờ VN.

Việc của phiên này:
1. Hỏi owner: giữ đủ C1–C3 hay bỏ C1 (decision log 11:45). Owner duyệt thì đóng băng final_config_v5 (ghi decision log,
   sha các module v3, runner `run_v3_api_v3.py`, cấu hình chạy Test-4 theo giao thức 2026-11-15 16:30).
2. Chuẩn bị hạ tầng chạy Test-4 một lần (v1 và v3 cùng chạy, ba mô hình), dry-run bằng backend giả, chưa đọc nội dung Test.
   Chạy thật sau 21/11 07:00, 2 phiên mỗi tài khoản; giữ `caffeinate -dimsu`, kiểm dung lượng đĩa trước.
3. Trong lúc chờ quota: viết bài (mô hình hình thức sang LaTeX, bảng Dev), Gemini để cuối.
4. Không chạy hay đọc Test-4 trước khi đóng băng v3. Không sửa runner/evaluator đã ghim, v1, Test cũ, số liệu đã có.
   Script đọc `results/rebuild_b` phải giải nén trước (`results/archive/rebuild_b/`).

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
