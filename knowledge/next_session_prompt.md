# Prompt cho phiên sau

Cập nhật: 2026-11-17. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): pin hỏng VĨNH VIỄN, chạy thẳng từ sạc 85 W. Chạy nhẹ: mỗi lúc một việc, nice -n 10, không mở app
nặng, KHÔNG chạy pytest toàn bộ (~1 giờ) mà chỉ test module đã đụng + lân cận. Không tự bật hay khởi động lại OmniRoute.
KHÔNG render hình hay biên dịch PDF trên máy: owner dùng Overleaf. Khi có chuỗi Kaggle chạy: giữ một
`caffeinate -dimsu` độc lập (kiểm `pmset -g assertions`), không để máy ngủ hay tắt màn hình.

Trạng thái (17/11 02:00): BrokerGuard v3 cho tạp chí Q4. Dev v4.1 (168 họ, Dev-val 42) là tập phát triển duy nhất;
Test-4 (seal `1f9b0070…`) niêm phong, H1 cổng: v3 < v1 về ASR (decision log 2026-11-15 18:20). Mốc Dev v4.1 đủ 12/12
(decision log 2026-11-16 18:00, 18:40, 20:30). V3P2 đang chạy bằng mô hình thật (`scripts/run_v3_api_v3.py`,
`build/kaggle/dev4_v3_chain.sh`); ablation V3P2-C1/-C2/-C3 trên Dev-val (490 fixture) đã ghi kế hoạch trước (decision log
2026-11-17 02:00) và do `build/kaggle/dev4_v3_follow.sh` / `dev4_v3_abl_follow.sh` tự chạy.

Việc của phiên này:
1. Kiểm tiến độ: `tail build/kaggle/dev4_v3_follow.log`, đếm `results/rebuild_c/dev4_1_V3P2_{model}/runs/A1/*/result.json`
   (đủ 1.960) và `dev4_1_V3P2-C{1,2,3}_val_{model}` (đủ 490), `kaggle kernels status`. Script dừng mà còn thiếu ca thì
   xem handoff "Đang làm" (folder notebook ghi trong `build/kaggle/dev4_folder_*`).
2. Chấm `scripts/evaluate_v3_v2.py` từng output, ghi số V3P2 so với D2P2 vào decision log (gây hại ca/họ, lộ câu cuối,
   utility thường/ủy quyền, chặn nhầm và lý do, max_steps/model_error, chi phí). Ablation đọc theo tiêu chí đã ghi trước.
3. Báo owner; owner duyệt thì đóng băng final_config_v5, rồi mới chạy Test-4 một lần. Gemini để cuối.
4. Không chạy hay đọc Test-4 trước khi đóng băng v3. Không sửa runner/evaluator đã ghim (`run_v3_api_v2.py`,
   `evaluate_v3_v2.py`), v1, Test cũ, số liệu đã có. Không chỉnh v3 theo số ablation trước khi owner xem.

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
