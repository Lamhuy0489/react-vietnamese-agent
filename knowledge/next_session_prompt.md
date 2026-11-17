# Prompt cho phiên sau

Cập nhật: 2026-11-18. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: pin đã sửa xong 17/11 (hết giới hạn chạy nhẹ). Vẫn: không render hình/biên dịch PDF trên máy (owner dùng
Overleaf), không tự khởi động lại OmniRoute. Khi chuỗi Kaggle chạy: giữ một `caffeinate -dimsu` độc lập (`pmset -g assertions`).

Trạng thái (18/11): final_config_v5 đã đóng băng (BrokerGuard v3 đủ C1–C3, sha `673f7af4…`, decision log 2026-11-17 19:25).
Test-4 CHƯA CHẠY ĐƯỢC CA NÀO: 2 tài khoản Kaggle mới (hieu1908 = kaggle7.json, lehung040324 = kaggle8.json) bị cấp máy CPU dù
chọn T4 (notebook thử `<owner>/gpu-check` báo NO_GPU, giờ GPU 0.00h/30h) — nhiều khả năng chưa xác minh số điện thoại. 7 tài
khoản cũ hết quota đến 21/11 07:00 giờ VN. Không có tiến trình nền nào chạy. Chi tiết và lệnh: handoff mục "Đang làm".

Việc của phiên này:
1. Hỏi owner đã xác minh số điện thoại 2 tài khoản mới chưa. Kiểm GPU bằng notebook thử `gpu-check` (handoff có cách tạo),
   đọc log và `kaggle quota`. Chỉ khi có GPU (hoặc sau 21/11 07:00 với tài khoản cũ) mới bật Test-4: xóa
   `build/kaggle/t4_folder_*` cũ, đẩy 4 notebook bằng `build/kaggle/t4_launch.sh` theo `t4_tags.json` (chọn owner có quota,
   tối đa 2 phiên mỗi tài khoản), bật supervisor `build/kaggle/t4_supervise.py`, vài phút sau kiểm `kernels status` RUNNING và
   quota bắt đầu trừ. Đừng suy notebook còn sống từ file cũ.
2. Khi Test-4 chạy: theo dõi bằng Monitor trên `build/kaggle/t4_supervise.log` (không poll qua nhiều lượt). Output đủ ca mà
   thiếu `_eval_v3.json` thì chấm `scripts/evaluate_v3_v3.py R`. Đủ hết thì phân tích đúng đăng ký trước (decision log
   2026-11-15 18:20): H1 (McNemar mức họ, v3 vs v1, 48 họ tĩnh) là cổng, rồi H2, H3 (Holm), H4; 24 ca thích nghi báo riêng.
   Ghi số vào decision log. Không chỉnh v3 hay chạy lại theo số Test-4 (chỉ chạy lại khi lỗi hạ tầng).
3. Trong lúc chờ: viết bài (mô hình hình thức sang LaTeX, bảng Dev v4.1). Sau Test-4: vòng tấn công thích nghi nhắm v3 trên
   họ Dev-val (owner/Minh soạn); Gemini để cuối (cần quyết định riêng, OmniRoute).
4. Không sửa file đã ghim trong final_config_v5 (src/react_agent, configs, runner/evaluator v4/v3, dữ liệu Test-4): sửa là
   Test-4 từ chối chạy. Không sửa file `.sh` đang chạy. Script đọc `results/rebuild_b` phải giải nén trước.

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
