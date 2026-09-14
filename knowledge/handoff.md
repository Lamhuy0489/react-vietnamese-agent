# Bàn giao phiên làm việc

Cập nhật: 2026-09-15. Chỉ dẫn hiện hành; lịch sử không thay thế mục này.

## Đang làm

**Shard 0 COMPLETE, terminal audit đã đạt**. Xem
[báo cáo](../docs/evaluation/phase5_grouped_v3_s0_report.md),
[audit](../experiments/manifests/phase5_grouped_v3_s0_audit01.json),
[summary](../experiments/manifests/phase5_grouped_v3_s0_summary01.json).
380 raw/2 remote hash khớp; 14 completed/recovered, 24 workers reaped (22 graceful,
2 terminate). Cả 14 trả ngay M208 đã có trong user instruction: 0 tool calls và
0 guard classification. Không coi completed là utility/guard quality; không retry.
Raw `results/phase5_grouped_v3_s0_download01` và audit/summary đã đóng.
Shards 1 SOURCEBINDING và 2 DATABASE đã submit v1, **COMPLETE** lúc kiểm
2026-09-14 18:41 UTC; source remote hashes khớp. Đã tải xong và audit raw tại
`results/phase5_grouped_v3_batch12_download01/raw_s1` và `raw_s2`.
Remote/status/log ở `results/phase5_grouped_v3_batch12_monitor01`.
[Submission 1](../experiments/manifests/phase5_grouped_v3_s1_submission01.json),
[submission 2](../experiments/manifests/phase5_grouped_v3_s2_submission01.json).
**Cả hai release audit đã đạt**: shard1 566 raw/2 remote, 4 completed/10 model_error;
shard2 678 raw/2 remote, 14 completed và 21 guard PRE/POST hợp lệ. 1.248 file scan
không credential values. [Báo cáo](../docs/evaluation/phase5_grouped_v3_batch12_report.md).
35 relevant tests/setup/Ruff/mypy394/knowledge đạt; worker source không đổi.
Tổng native coverage 42/112 (37,5%), không phải Phase5 acceptance.

**Shards 3 ENCODED / 4 LINKPAGE v1 COMPLETE/audit, kiểm 20:02 UTC ngày 2026-09-14**.
Kernel IDs 134383821 / 134383829; actual handles dùng `...-shard-3` / `...-shard-4`.
[Báo cáo/URL/receipts](../docs/evaluation/phase5_grouped_v3_batch34_report.md).
Source `0d86536`, GitHub evidence `7078593` đã push trước submit. 175 source pins,
hai wrapper/metadata pins và mã tải ngược đều khớp; quota trước gửi 26,79h,
Dataset private ready/v1, offline T4x2/14.400s. 914 raw/4 remote files hash khớp,
918 file scan/0 credentials; hai release audits/shard byte-identical.
Shard3 14 completed nhưng 0 tool calls, final nói đã gửi mã mà không mock send;
shard4 4 completed/10 model_error, 10 PRE malformed JSON/4 POST backend failure.
28 recovered/48 reaped (44 graceful/4 terminate). **Tổng 70/112 audited (62,5%)**,
50 completed/20 model_error; Phase5 vẫn 4/7≈57%. 35 focused tests/setup/Ruff/
mypy394/knowledge đạt; full frozen-worker QA giữ nguyên, không chạy lại.
Raw submission/access/monitor/download/audit/summary lưu theo báo cáo; không ghi đè.
API current_version=1 đã xác minh; last_run_time bất thường được giữ nguyên,
không dùng thay observation timestamp hoặc native timing.

Nền đã chốt và lịch sử submission (RUNNING dưới đây đã được terminal thay thế):

Package v3 source `0d86536` đã chạy xong exact preflight; mỗi layout archive và
expanded đạt 8 tools, 21 clean Dummy, 112 grouped stub/resume, 128 module origins.
4.357 hashes recheck khớp, 4.360 files secret scan/0 matches. Xem
[report v3](../docs/evaluation/phase5_grouped_package_v3_report.md) và
[preflight receipt](../experiments/manifests/phase5_grouped_package_v3_preflight01.json).
**Full QA đã đạt 3.113 pass/1 skip/1.060,05s** tại
`results/phase5_grouped_package_v3_qa01`; setup/Ruff/mypy392/knowledge đạt.
555 source/7 raw/169 data hashes kiểm lại khớp; output đã đóng, không chạy lại.
[QA receipt](../experiments/manifests/phase5_grouped_package_v3_cpu01.json).
Source/evidence đã push GitHub `93dc9a2`. **Shard 0 đã submit v1 và đang RUNNING**:
[notebook thực tế](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-0),
[submission receipt](../experiments/manifests/phase5_grouped_v3_s0_submission01.json).
14 ca, private/offline T4x2, timeout 14.400s; không submit lại. Source remote khớp
hash package. Kaggle đổi alias `...-s0` thành `...-shard-0` theo title.
Quota trước submit: 29,02h; Dataset private ready/v1, Qwen model v1.
Raw monitor: `results/phase5_grouped_v3_s0_monitor02`; source/metadata pull thành
công khi bỏ `/1`, versioned pull trả 403 dù status v1 hoạt động. Chưa có log
nội dung; không suy đoán số ca hoặc nguyên nhân từ log rỗng.

Bộ kiểm terminal local mới: `scripts/audit_phase5_grouped_gpu_v3.py`,
[audit notes](../docs/evaluation/phase5_grouped_gpu_v3_audit_notes.md); 32 focused
tests đạt, setup/Ruff/mypy393/knowledge đạt; source `05da583`,
[focused receipt](../experiments/manifests/phase5_grouped_release_auditor_v3_cpu01.json).
Không thay frozen worker. Monitor04 lúc **14:59:33 UTC** cho biết RUNNING,
failureMessage=null; monitor03 files=[], log rỗng. Chưa có kết quả để audit.
Không chạy lại QA/preflight đã chốt; việc kế tiếp duy nhất của shard này là
kiểm terminal, tải output mới và chạy read-only release auditor.

Mốc CPU nền trước đó (đã đóng):

Đã chốt [grouped Dev runner/checkpoint v1](grouped_runner_v1.md), source `354b75b`.
27 focused tests đạt/130,62s; 112 ca/8 shards, resume/tampering/failure retention
đã kiểm. Full QA **3.055 pass/1 skip/973,70s**; setup/Ruff/mypy381/knowledge đạt.
537 source/1.783 raw/169 data hashes kiểm lại khớp; selected receipt đã lưu.
Output `results/phase5_grouped_runner_v1_cpu01` đã đóng. Không chạy trùng, sửa
source đã khóa hoặc ghi thêm raw của mốc này.

## Bước tiếp theo

Native v2 source `3486dbf` đã ghép. **Thu hồi kết luận package/import isolation**
của hai receipt cũ: overlay nằm dưới `configs`, editable install đã cung cấp
module từ repo. Giữ nguyên raw/receipt. Xem phần đính chính trong báo cáo native.
Package v3 preflight đã đạt; 14 regression tests đạt, Ruff/mypy392 đạt trước freeze.
Trạng thái native mới nhất ở đầu trang: 0–4 audited; 5–7 chưa gửi.

1. CPU QA và preflight đã hoàn tất; không chạy lại. Selected QA receipt đính chính
   scope Test của full historical suite, không coi flag cũ là filesystem audit.
2. Shards 0–4 đã terminal/audit; raw và summaries đã đóng, không tải/rerun trùng.
   Sau GitHub push và live quota/Dataset check, gửi shards5 QUERYLEAK/6 QUOTED
   cùng package. Audit từng shard trước khi gửi shard7 ROWLIST.
3. Theo [contract v3](../docs/architecture/phase5_grouped_package_v3_contract.md),
   giữ source `0d86536`, package đã khóa, timeout 14.400s mỗi shard; ghi URL/version
   thực tế như receipts trên. Audit từng shard trước khi mở rộng shard 5–7.
4. Báo matched Dev guard structured-output/Pre/Post, lỗi, startup/generation/
   end-to-end timing và lifecycle; không retry ngữ nghĩa hoặc mở Test để tuning.

Pending access: không cần tài khoản mới. Owner Kaggle thực tế `huylmhuhu`;
phải kiểm live quyền/quota/private mounts trước submission. Snapshot quota cũ
trong sổ tài nguyên không phải reservation. Không cycling credentials hoặc làm
public tài nguyên private. Tác vụ model nặng chỉ chạy Kaggle.

## Bằng chứng

- [Báo cáo runner hiện hành](../docs/evaluation/phase5_grouped_runner_v1_report.md).
- [Grouped CPU receipt](../experiments/manifests/phase5_grouped_runner_v1_cpu01.json),
  SHA-256 `6233354ab9445569d83c020f4b3a4f1f4d65bcd81fec4a85bea53ea80243f9f3`.
- [Native v2 preflight](../docs/evaluation/phase5_grouped_native_v2_report.md) và
  [receipt](../experiments/manifests/phase5_grouped_native_v2_preflight01.json).
- [SQL CPU prerequisite](../experiments/manifests/phase5_sql_scope_v5_cpu01.json),
  source `3667529`: 3.028 pass/1 skip, 531 source/463 raw/169 data hashes khớp.
  Output đã đóng, không chạy trùng/ghi thêm.
- [Native diagnostics CPU](../experiments/manifests/phase5_native_diagnostics_v1_cpu01.json)
  đã chốt; chưa chứng nhận observer chạy native GPU.
- [Native document diagnostic](../experiments/manifests/phase5_document_gpu_v1_audit01.json):
  COMPLETE/audit, A2–A6 INVALID_OUTPUT; không retry. [Sổ link](kaggle_resources.md).
- [Lịch sử nguyên bản trước thu gọn](history_20260914_grouped_runner_handoff.md);
  không dùng câu “đang làm” cũ để quyết định chạy lại.

## Giới hạn

Phase 5 chưa accepted, aggregate 4/7≈57%. CPU scripted/fake guard không đo
utility/ASR/FPR. Public Dev ROWLIST thiếu explicit column grants nên sáu ca
A4–A6 không đọc được; giữ kết quả, không sửa data/cấp quyền từ oracle.
Không Test/private GT hoặc mock network I/O. Entitlement v1 receipt có hash
pytest.log sai: giữ lịch sử, không lấy valid=true làm nghiệm thu.

Giữ nguyên thay đổi của người dùng ngoài phạm vi: `plan/phase6.md`–`phase9.md`,
`docs/BAO_CAO_TIEN_DO_DO_AN.md`/PDF và `docs/figures/`; không stage/xóa.
