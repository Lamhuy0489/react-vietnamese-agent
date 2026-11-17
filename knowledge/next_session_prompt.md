# Prompt cho phiên sau

Cập nhật: 2026-11-17 19:40. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: pin đã sửa xong 17/11 (hết giới hạn chạy nhẹ). Vẫn: không render hình/biên dịch PDF trên máy (owner dùng
Overleaf), không tự khởi động lại OmniRoute. Khi chuỗi Kaggle chạy: giữ một `caffeinate -dimsu` độc lập (`pmset -g assertions`).

Trạng thái (17/11 19:35): final_config_v5 đã đóng băng (BrokerGuard v3 đủ C1–C3, sha `673f7af4…`, decision log 19:25).
Test-4 đang chạy MỘT LẦN: 3 mô hình × {A0, P2, PRG, D2P2, V3P2, V3P2-C1/-C2/-C3} × 560 ca + 24 ca thích nghi, trên
hieu1908 và lehung040324; supervisor `build/kaggle/t4_supervise.py` (sự kiện `build/kaggle/t4_supervise.log`).

Việc của phiên này:
1. Kiểm Test-4: supervisor còn sống không (`pgrep -fl t4_supervise`), `tail build/kaggle/t4_supervise.log`, đếm ca từng
   output (lệnh trong handoff). Supervisor chết thì bật lại (lệnh trong handoff). Đừng suy notebook còn sống từ file cũ.
2. Output nào đủ ca mà thiếu `_eval_v3.json` thì chấm `scripts/evaluate_v3_v3.py R`. Đủ hết thì phân tích đúng đăng ký
   trước (decision log 2026-11-15 18:20): H1 (McNemar mức họ, v3 vs v1, 48 họ tĩnh) là cổng, rồi H2, H3 (Holm), H4; 24 ca
   thích nghi báo riêng. Ghi số vào decision log. Không chỉnh v3 hay chạy lại theo số Test-4 (chỉ chạy lại khi lỗi hạ tầng).
3. Sau Test-4: vòng tấn công thích nghi nhắm v3 trên họ Dev-val (owner/Minh soạn, báo riêng); viết bài (mô hình hình
   thức sang LaTeX, bảng Dev v4.1 và Test-4); Gemini để cuối (cần quyết định riêng, OmniRoute).
4. Không sửa file đã ghim trong final_config_v5 (src/react_agent, configs, runner/evaluator v4/v3, dữ liệu Test-4): sửa là
   Test-4 từ chối chạy. Script đọc `results/rebuild_b` phải giải nén trước (`results/archive/rebuild_b/`).

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
