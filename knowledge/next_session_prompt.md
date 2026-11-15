# Prompt cho phiên sau

Cập nhật: 2026-11-15. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG (bắt buộc): máy hỏng pin, chạy thẳng từ sạc 85 W. Không mở app nặng. Mỗi lúc một tiến trình nặng, nice -n 10.
Không tự bật hay khởi động lại OmniRoute (owner bật). KHÔNG render hình hay biên dịch PDF trên máy: owner dùng Overleaf.

Trạng thái (15/11 23:50): mở rộng bài thành BrokerGuard v3 cho tạp chí Q4 (thiết kế
`docs/project/brokerguard_v3_extension_design.md`). Dev v4.1 (`data/adversarial/release_dev4_1`, 168 họ, Dev-val 42) là
tập phát triển duy nhất. Test-4 (`data/adversarial/release_test4`, seal `1f9b0070…`, commit a1711a6) đã niêm phong; đăng
ký trước ở decision log 2026-11-15 18:20 (H1 cổng: v3 < v1 về ASR, McNemar mức họ). Test-4 do mã sinh từ spec, owner và
Minh rà; bài phải ghi đúng như vậy và không báo κ giữa người gắn nhãn.

Việc của phiên này:
1. Kiểm mốc Dev v4.1 (12 notebook, mỗi notebook một cấu hình, sổ Kaggle mục 15/11 23:50): `build/kaggle/dev4_progress.sh`,
   `build/kaggle/dev4_watch.log`, `kaggle kernels status`. Supervisor `build/kaggle/dev4_supervise.sh` và
   `build/kaggle/dev4_kaguard.sh` chạy dưới caffeinate; nếu đã tắt mà còn việc thì bật lại (handoff "Đang làm"). Job xong
   khi đủ 1960 và có `_eval_v2.json` mới hơn mọi ca. Ghi số (hai cách chấm, chặn nhầm, xác nhận, chi phí) vào decision
   log; xem max_steps/model_error của Qwen trước khi dùng utility cho H2. Giết chuỗi thì giết cả cây tiến trình.
2. Viết C1: bộ trích chính sách ý định P(u) tất định (cực tính phủ định VI/EN, khớp đích theo token, quyền theo loại hành
   động, ca không rõ = cần xác nhận = từ chối), file mới trong `src/react_agent/security_v3/`, có test; chỉ dùng Dev-train,
   chọn cấu hình trên Dev-val. Rồi C2 (nhãn theo giá trị, R-Flow v2), C3 (ghim tham số), ablation, đóng băng final_config_v5.
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
