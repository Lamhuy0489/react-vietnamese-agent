# Prompt cho phiên sau

Cập nhật: 2026-11-16. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): pin hỏng VĨNH VIỄN, chạy thẳng từ sạc 85 W. Chạy nhẹ: mỗi lúc một việc, nice -n 10, không mở app
nặng, KHÔNG chạy pytest toàn bộ (~1 giờ) mà chỉ test module đã đụng + lân cận. Không tự bật hay khởi động lại OmniRoute.
KHÔNG render hình hay biên dịch PDF trên máy: owner dùng Overleaf.

Trạng thái (16/11 15:30): BrokerGuard v3 cho tạp chí Q4 (thiết kế `docs/project/brokerguard_v3_extension_design.md`).
Dev v4.1 (`data/adversarial/release_dev4_1`, 168 họ, Dev-val 42) là tập phát triển duy nhất. Test-4 (seal `1f9b0070…`)
niêm phong; H1 cổng: v3 < v1 về ASR, McNemar mức họ (decision log 2026-11-15 18:20). Mốc Dev v4.1: Qwen A0, P2 xong
(decision log 2026-11-16 11:15), 10 cấu hình còn chạy. Runtime v3 C1+C2+C3 xong code, 52 test
(`src/react_agent/security_v3/brokerguard_v3_v1.py`); phát lại oracle Dev-val: hại v1 25/210 -> v3 2/210, utility bằng
v1 (decision log 2026-11-16 15:30). Chưa nối runner, chưa chạy v3 bằng mô hình thật.

Việc của phiên này:
1. Kiểm mốc Dev v4.1: `build/kaggle/dev4_progress.sh`, `tail build/kaggle/dev4_watch.log`, `kaggle kernels status`.
   Supervisor/kaguard dưới caffeinate; tắt mà còn việc thì bật lại (handoff "Đang làm"). Job xong khi đủ 1960 và có
   `_eval_v2.json` mới hơn mọi ca; ghi số từng cấu hình vào decision log (hai cách chấm, chặn nhầm, xác nhận, chi phí,
   max_steps/model_error). Giết chuỗi thì giết cả cây.
2. Khi không còn chuỗi nào gọi `run_v3_api_v2.py`: thêm `--defense v3p2` và `v3p2-c1/-c2/-c3` (chỉ thêm khóa, như handoff),
   test dry-run, chạy trên Kaggle cùng cách mốc. Rồi đóng băng final_config_v5 (owner duyệt) và chạy Test-4 một lần.
3. Benchmark vi mô của broker làm cùng code v3. Gemini để cuối, sau khi ba mô hình mở xong.
4. Không chạy hay đọc Test-4 trước khi đóng băng v3. Không sửa runner/evaluator đã ghim, v1, Test cũ, số liệu đã có.

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
