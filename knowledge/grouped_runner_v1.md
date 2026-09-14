# Grouped Dev runner/checkpoint v1

Cập nhật 2026-09-14. CPU plumbing, không phải kết quả model hoặc nghiệm thu Phase 5.

## Đã chốt CPU

Source `354b75b`: runner runtime v10 cho 112 khóa `variant_id__level`, tám shard,
mỗi shard một cặp attack/benign × A0–A6. Lượt phát triển đạt 27 tests/137,67s;
lượt lưu bằng chứng đạt 27 focused/130,62s và full **3.055 pass/1 skip/973,70s**.
Skip duy nhất là native tqdm không có trong môi trường local; không giả lập pass.
Setup/Ruff/mypy381/knowledge đạt. Kiểm độc lập 537 source/1.783 raw/169 data hashes
khớp. [Selected receipt](../experiments/manifests/phase5_grouped_runner_v1_cpu01.json)
SHA-256 `6233354ab9445569d83c020f4b3a4f1f4d65bcd81fec4a85bea53ea80243f9f3`.
Output `results/phase5_grouped_runner_v1_cpu01` đã đóng; không chạy trùng/ghi thêm.
Không còn QA đang chạy; không có GPU job mới.
Quét credential values trước lưu: 2.330 files/four values, zero matches.

## Cơ chế và giới hạn

- Lịch dùng đúng tám nhóm Dev đã chọn trước; không mở Test hoặc private oracle.
- Mỗi ca có môi trường/worker riêng. A0/A1 không khởi tạo guard; các mức sau dùng
  guard SAFE cố định. Agent chỉ phát public trigger rồi final cố định.
- Identity khóa commit, Dev/environment/fixture hashes, catalog, task, level,
  runtime/config/generation và synthetic backend revision. Metadata chọn mẫu
  không đưa vào prompt. Không đo ASR/FPR hoặc chất lượng câu trả lời ở lượt này.
- Resume kiểm toàn bộ checkpoint trước khi chạy ca mới. Sai hash/config/key,
  thư mục dở, khoảng trống, file lạ hoặc symlink đều bị từ chối; không tự sửa.
- Ca terminal lỗi vẫn giữ nguyên, không retry ngữ nghĩa. Fault-control riêng
  cố ý tạo parse_failure; không trộn với 112 ca lịch chuẩn.
- Raw/checkpoint hashes là kiểm tra toàn vẹn, không phải chữ ký chống người có
  quyền sửa đồng thời toàn bộ artifacts/receipt. Source receipt phải được giữ
  riêng trên GitHub. Test identity dùng commit sentinel `a` × 40; QA receipt
  gắn commit/source hashes thực tế, không gọi sentinel là commit inference.
- CLI resume yêu cầu cùng Git HEAD; sau commit mới dùng audit-only để đọc lịch
  sử. Không bỏ kiểm tra identity hoặc gán commit cũ cho mã nguồn mới để resume.
- Native dispatch tắt; CPU terminal/guard SAFE không chứng minh chất lượng LLM.

## Lệnh

Từ repo, với source commit thích hợp và output mới:

```sh
.venv/bin/python scripts/run_phase5_grouped_dev_cpu.py --output results/grouped_dev_example_shard0 --shard 0 --max-new-tasks 1
.venv/bin/python scripts/run_phase5_grouped_dev_cpu.py --output results/grouped_dev_example_shard0 --shard 0 --resume
.venv/bin/python scripts/run_phase5_grouped_dev_cpu.py --output results/grouped_dev_example_shard0 --shard 0 --audit-only
```

Đây là ví dụ, không có bằng chứng đã chạy những output tên example.
Không dùng tên output/receipt đã tồn tại cho một lượt QA mới.
Raw CPU nằm local dưới `results/` và không track Git; bạn cùng máy đọc trực tiếp
được. Clone GitHub chỉ có source, report và selected receipt sau khi commit,
không tự tải được raw CPU. Chưa upload hoặc công khai artifacts này lên Kaggle.

## Bước tiếp

QA CPU01 đã chốt; tiếp ghép adapter native riêng: agent/guard factory, sanitized
diagnostics, per-request timing/token counts, PID/VRAM recovery và auditor vào
cùng lịch Dev. Preregister identity native và thời lượng/shard trước upload;
không bật native bằng cách đổi nhãn CPU. Kiểm exact archive/expanded offline
package trước Kaggle, xác nhận source đã push GitHub. Không sửa prompt/policy
theo Test, không retry kết quả model cũ. Không cần tài khoản mới; quyền/quota
Kaggle phải kiểm live trước submission, không dùng snapshot cũ như reservation.

## Liên kết

- [Contract](../docs/architecture/phase5_grouped_runner_v1_contract.md).
- [Báo cáo và giới hạn](../docs/evaluation/phase5_grouped_runner_v1_report.md).
- [SQL scope/runtime prerequisite](sql_scope_v5.md).
- [Native diagnostics đã kiểm CPU](guard_diagnostics_v1.md).
- [Notebook/Dataset hiện có](kaggle_resources.md): lượt này chưa tạo tài nguyên mới.
