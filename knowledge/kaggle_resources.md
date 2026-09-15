# Sổ tra cứu Kaggle của đồ án

Cập nhật 2026-09-15 từ receipts/report đã lưu trong Git và live submission checks.
Đây là **memory phát
triển cho nhóm**, không đưa vào prompt benchmark. Trạng thái dưới đây là mốc
bằng chứng lịch sử, không phải kiểm tra trực tuyến lại mọi URL hôm nay.

Các URL code/Dataset/model có receipts đối chiếu trong `experiments/manifests/`.
Chưa khẳng định mọi URL vẫn mở được với tài khoản khác.

## Bạn mới tham gia bắt đầu ở đâu?

1. Đọc [trạng thái hiện tại](current_status.md) và [bàn giao](handoff.md).
2. Source chính thức: [GitHub main](https://github.com/Lamhuy0489/react-vietnamese-agent).
3. Kaggle là máy chạy inference. Tài khoản sở hữu các tài nguyên bên dưới là
   `huylmhuhu`; khác với tên GitHub `Lamhuy0489`.
4. Notebook/Dataset được giữ private. Quyền GitHub không tự cấp quyền Kaggle:
   nếu bạn Minh dùng tài khoản Kaggle riêng thì chủ tài nguyên cần cấp quyền
   cộng tác phù hợp. Không chép API key/token/mật khẩu vào Git hoặc trang này,
   không chuyển public chỉ để mở được link. 403/404 có thể là thiếu quyền.

## Mốc hiện hành — đọc mục này trước

**Observer native v2 v1 COMPLETE/audit**, kiểm2026-09-15 11:52:53UTC;
ID134481763. [Notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-observer-native-v2),
[report và đường dẫn raw](../docs/evaluation/phase5_observer_native_v2_run.md),
[submission](../experiments/manifests/phase5_observer_native_v2_submission01.json),
[terminal/version/source receipt](../experiments/manifests/phase5_observer_native_v2_terminal01.json),
[releaseaudit](../experiments/manifests/phase5_observer_native_v2_audit01.json),
[summary](../experiments/manifests/phase5_observer_native_v2_summary01.json).
Requested=actual `huylmhuhu/react-vn-observer-native-v2`, source`c0930bf`,v1.
[Datasetguard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1ready, private; GitHubcf871a3pushed trước gửi.4tasksCALC/DOC×A2/A6,T4x2/offline.
Mã tải ngược khớp trước/sau download;159source/158raw/2remote verified.
4model_error;2valid/4fenced guardresponses,8reaped/4recovered nhưng3forcedshutdown.
Raw `results/phase5_observer_native_v2_terminal02`, hai reports01/02 đã đóng;
chi tiết timing/receipts trong report. Không gửi lại. Quyền truy cập private giữ nguyên.

### Bare-JSON candidate preflight

Source `f7492fae80876891237fcd37084e79ed5af60a2e`; [CPU preflight report](../docs/evaluation/phase5_guard_bare_json_preflight_v1.md)
and [manifest](../experiments/manifests/phase5_guard_bare_json_package_v1_preflight01.json).
Requested notebook `huylmhuhu/react-vn-guard-bare-json-v1` (not submitted yet),
private/offline T4×2/14.400s, same guard15 Dataset v1 and Qwen mounts. Access check
2026-09-15: GPU22.80h remaining, Dataset ready/current v1. CPU package has no
model loads/GPU/Test access; candidate valid=4/4, injected trailing/fenced=0/4
as expected plumbing controls. Preserve candidate failure identities and submit
at most once after GitHub/source/package verification.

Lịch112ca trước đó:

**Cả8notebooks đã terminal/audit,112/112ca; không còn jobpending.**
[Báo cáo tổng](../docs/evaluation/phase5_grouped_v3_complete_report.md).
ROWLIST R3 đã COMPLETE lúc2026-09-15 05:53:41UTC, v1/ID134443063;
[terminal/version/hashes](../experiments/manifests/phase5_grouped_v3_s7_terminal01.json),
[audit](../experiments/manifests/phase5_grouped_v3_s7_audit01.json).
Actual notebook/Dataset/source vẫn như dưới;614raw/2remote hashes khớp.
Nguồn `0d86536`, Datasetguard15v1, GitHubevidence875399d trước submit giữ nguyên.
Không dùng các câuRUNNINGlịch sử dưới đây để submit/tải lại.

### Lịch sử admission trước terminal

**Shard7 ROWLIST R3 v1 RUNNING**, kiểm2026-09-15 05:06:57UTC:
[notebook thật](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-rowlist-r3),
kernel ID134443063; [submission03](../experiments/manifests/phase5_grouped_v3_s7_submission03.json),
[admission report](../docs/evaluation/phase5_grouped_v3_s7_admission_report.md).
Source `0d865365b7881144756f804441ca24ed48935f7f`, GitHub evidence875399d trước
push; [Dataset guard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1private/ready, modelv1, offlineT4x2/14.400s/image pins giữ nguyên. Quota trước
attempt02/03 snapshot23,83h. Source tải ngược khớp. R3=admissionattempt3,
không phải securitylevelA3; vẫn đủ14taskA0–A6 của shard7. Không submit lại.
Giữ hai attempt cũ: hết2GPUslots rồiHTTP409; chúng không có confirmed run/version.
Tên mới chỉ thay id/title để phục hồi admission, chưa có terminal result.

### Shards5/6 đã terminal audit

**Grouped v3 shards5/6 v1 COMPLETE/audit**, kiểm2026-09-15 04:51UTC:

| Notebook thật | Version / ID | Bằng chứng |
|---|---|---|
| [shard-5 QUERYLEAK](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-5) | v1 / 134393202 | [submission](../experiments/manifests/phase5_grouped_v3_s5_submission01.json) |
| [shard-6 QUOTED](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-6) | v1 / 134393213 | [submission](../experiments/manifests/phase5_grouped_v3_s6_submission01.json) |

[Report và raw paths](../docs/evaluation/phase5_grouped_v3_batch56_report.md).
Source `0d865365b7881144756f804441ca24ed48935f7f`, GitHub evidence `80a8bae` trước
push; [Dataset guard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
private/ready/v1; quota25,34h trước gửi. Offline T4x2/model v1/14.400s/image pins
không đổi. Mã tải ngược khớp. Requested `...-s5`/`...-s6` khác actual handles.
Terminal/audit:502+662raw/4remote hashes khớp;scan1168files/0credentials.
[Terminal5](../experiments/manifests/phase5_grouped_v3_s5_terminal01.json),
[terminal6](../experiments/manifests/phase5_grouped_v3_s6_terminal01.json); report
có audits/summaries/timing. Tổng98/112audited, không phải semantic success.
Không submit lại5/6. Shard7 hai lượt đầu lỗi: hết2GPUslots rồiHTTP409;
[admission report](../docs/evaluation/phase5_grouped_v3_s7_admission_report.md).
Tên launcher03 `huylmhuhu/react-vn-grouped-dev-v3-rowlist-r3` đã v1RUNNING
theo mục đầu trang; giữ nguyên danh tính hai attempt lỗi trước.

### Grouped v3 shards3/4 — terminal đã kiểm

**Grouped v3 shards 3/4 v1 COMPLETE/audit**, kiểm 2026-09-14 20:02 UTC:

| Notebook thật | Version / ID | Bằng chứng |
|---|---|---|
| [shard-3 ENCODED](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-3) | v1 / 134383821 | [submission/status/source hash](../experiments/manifests/phase5_grouped_v3_s3_submission01.json) |
| [shard-4 LINKPAGE](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-4) | v1 / 134383829 | [submission/status/source hash](../experiments/manifests/phase5_grouped_v3_s4_submission01.json) |

[Report và raw paths](../docs/evaluation/phase5_grouped_v3_batch34_report.md).
Source `0d865365b7881144756f804441ca24ed48935f7f`, GitHub evidence `7078593` trước
push. Cùng [Dataset guard15 v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
đã live ready/v1; private/offline T4x2, model v1, timeout 14.400s; quota snapshot
26,79h trước submit. Mã tải lại khớp bản khóa; live current_version=1 đúng IDs.
Requested aliases `...-s3`/`...-s4` không phải handle thật.
[Terminal3](../experiments/manifests/phase5_grouped_v3_s3_terminal01.json),
[terminal4](../experiments/manifests/phase5_grouped_v3_s4_terminal01.json) có status/
version/hash/scan; report liên kết audit và summaries. 380+534 raw/4 remote hashes
khớp, scan918files/0credentials. Shard3 0tools; shard4 10 model_error do guard JSON.
Tổng70/112 audited, chưa Phase5 acceptance. API last_run_time bất thường không
dùng cho thời gian chạy; giữ nguyên để đối chiếu. Shards5/6 RUNNING ở đầu trang.
Shards0–2 COMPLETE/audit ở dưới; không submit trùng. Quyền GitHub không cấp quyền
Kaggle private; không đổi public hoặc lưu credentials để chia sẻ.

### Mốc trước — document runtime và security runtime

Ngày 2026-09-14 đã gửi **version 1** notebook private mới
[react-vn-document-runtime-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-document-runtime-v1).
Source `54aa3ec`, GitHub evidence `8836e9c` đã push trước submit; T4/7200s/offline.
Dataset [react-vn-guard15-probe-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1 đã kiểm live private/ready. [Submission receipt](../experiments/manifests/phase5_document_gpu_v1_submission01.json),
[report](../docs/evaluation/phase5_document_diagnostic_v1_report.md) và
[memory](document_diagnostic_v1.md). **Terminal COMPLETE, audit đạt** ngày 2026-09-14:
[GPU receipt](../experiments/manifests/phase5_document_gpu_v1_audit01.json),
[terminal summary](../experiments/manifests/phase5_document_gpu_v1_terminal01.json).
261raw/2remote hashes khớp; 7 reads, A0/A1 completed, A2–A6 model_error do guard
INVALID_OUTPUT rồi pair retirement. 8GRACEFUL/4TERMINATE, 7recovered; chưa quality/
Phase5 acceptance. Không submit trùng. Quyền GitHub không tự cấp quyền notebook.

Chuẩn bị local mới nhất: [shutdown package v2](shutdown_package_v2.md) đã đạt
CPU/exact mounts ngày 2026-09-14, **chưa submit**. Tên v2 trong metadata là tên
dự kiến, không có notebook URL/version mới để thay mốc native v1 bên dưới.

| Tài nguyên | Link | Phiên bản/bằng chứng |
|---|---|---|
| Notebook runtime A0–A6 | [react-vn-security-runtime-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-security-runtime-v1) | v1 COMPLETE; [GPU report](../docs/evaluation/phase5_security_runtime_gpu_v1_report.md), [receipt](../experiments/manifests/phase5_security_runtime_gpu_v1_audit01.json) |
| Dataset dùng chung Phase 5 | [react-vn-guard15-probe-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1) | v1 private/ready đã kiểm trước run; source bundle, guard snapshot và offline wheels; [preflight](../experiments/manifests/phase5_security_runtime_v1_preflight03.json) |
| Model mount agent hiện hành | [Qwen2.5 7B Instruct / Transformers / v1](https://www.kaggle.com/models/qwen-lm/qwen2.5/transformers/7b-instruct/1) | Model mount, **không phải Dataset của nhóm**; identity/file hashes nằm trong receipt |

V1 hoàn tất không có nghĩa Phase 5 đã nghiệm thu: 7 terminal/recovery, nhưng
0 tool calls/0 guard calls, 12 worker TERMINATE/-15. Không chạy lại để chọn câu
trả lời đẹp hơn. Source inference `372d685`; raw local
`results/phase5_security_runtime_gpu_v1_output01`; source tải ngược
`results/phase5_security_runtime_gpu_v1_remote02`. Raw generated không track Git;
người clone mới lấy output từ notebook, đối chiếu hash với receipt trước dùng.

## Notebook lịch sử Phase 5

Không chọn notebook chỉ vì tên mới hoặc status COMPLETE. Đọc cột bằng chứng;
model quality, lỗi hạ tầng, native OOM và thử nghiệm transport là các mục khác nhau.
Những notebook này dùng Dataset Phase 5 chung ở trên; kiểm mount/version trong
receipt của đúng lượt, không tự nâng phiên bản.

| Notebook | Vai trò / tài liệu đối chiếu |
|---|---|
| [guard15-probe-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard15-probe-run-v1) | [Guard GPU đầu tiên](guard_gpu_probe_v1.md); không dùng làm chứng nhận chất lượng guard |
| [guard-cancel-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard-cancel-run-v1) | [Cancellation và recovery](guard_cancellation_v1.md) |
| [pair-gpu-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-gpu-v1) | [Agent/guard cùng GPU](pair_gpu_v1.md) |
| [pair-cancel-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-cancel-v1) | [Pair cancellation](pair_cancellation_v1.md) |
| [pair-ipc-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-ipc-v1) | [IPC diagnostic](pair_ipc_v1.md) |
| [pair-progress-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-progress-v1) | [Progress-lock diagnostic](pair_progress_v1.md) |
| [policy-native-compat-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-policy-native-compat-v1) | [Native-library CPU compatibility](policy_native_compat_v1.md), không phải GPU benchmark |
| [context-policy-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-context-policy-v1) | [Lỗi factory topology lịch sử](context_policy_gpu_v1.md) |
| [context-policy-v2](https://www.kaggle.com/code/huylmhuhu/react-vn-context-policy-v2) | [OOM sau readiness](../docs/evaluation/phase5_context_policy_v2_oom_review.md) |
| [sdpa-tensor-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-sdpa-tensor-v1) | [SDPA tensor diagnostic](sdpa_tensor_v1.md) |
| [efficient-stress-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-efficient-stress-v1) | [Efficient stress](efficient_stress_v1.md) |
| [ordinary-pair-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-ordinary-pair-v1) | [Lượt lỗi giữ nguyên](../experiments/manifests/phase5_ordinary_pair_gpu_v1_error01.json) |
| [ordinary-pair-t4x2-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-ordinary-pair-t4x2-v1) | [A/B/A native transport evidence](ordinary_pair_gpu_v1.md) |

## Terminal audit ngày 2026-09-14

### Grouped Dev native v3 — shards 1/2 COMPLETE/audit

Kiểm 2026-09-14 18:41 UTC (2026-09-15 tại Việt Nam):

| Notebook thật | Version / ID | Trạng thái / bằng chứng |
|---|---|---|
| [shard-1 SOURCEBINDING](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-1) | v1 / 134350547 | COMPLETE; [submission](../experiments/manifests/phase5_grouped_v3_s1_submission01.json), [audit](../experiments/manifests/phase5_grouped_v3_s1_audit01.json) |
| [shard-2 DATABASE](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-2) | v1 / 134350561 | COMPLETE; [submission](../experiments/manifests/phase5_grouped_v3_s2_submission01.json), [audit](../experiments/manifests/phase5_grouped_v3_s2_audit01.json) |

Source `0d865365b7881144756f804441ca24ed48935f7f`, GitHub push `2a8df8d` trước
submit. Cùng [Dataset guard15 v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1),
private/offline T4x2, Qwen model v1. Requested aliases `...-s1`/`...-s2` không phải
handle thật. 566+678 raw/4 remote hashes verified. [Report/summary/scan links](../docs/evaluation/phase5_grouped_v3_batch12_report.md).
Shard1 10 model_error do guard JSON syntax; shard2 21 valid guard responses.
Không retry; chưa suy ra utility/ASR/FPR. Shards 3/4 đã RUNNING theo mục hiện hành.

### Grouped Dev native v3 — shard 0 COMPLETE/audit

[Notebook thực tế](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-0)
**v1, COMPLETE**, kiểm ngày 2026-09-14 lúc 15:02:53 UTC; kernel ID `134340826`.
Alias yêu cầu `huylmhuhu/react-vn-grouped-dev-v3-s0` đã được Kaggle đổi theo title.
Source `0d865365b7881144756f804441ca24ed48935f7f`, push GitHub qua `93dc9a2` trước
submission. Dataset guard15 v1 private và model Qwen v1 như dưới. 14 ca/shard0,
T4x2/offline/private, timeout 14.400s. [Submission receipt](../experiments/manifests/phase5_grouped_v3_s0_submission01.json),
[report](../docs/evaluation/phase5_grouped_package_v3_report.md).
Remote source hash khớp; pull có `/1` trả 403 nhưng pull handle không version
thành công. [Terminal report](../docs/evaluation/phase5_grouped_v3_s0_report.md),
[audit](../experiments/manifests/phase5_grouped_v3_s0_audit01.json),
[summary](../experiments/manifests/phase5_grouped_v3_s0_summary01.json),
[preservation](../experiments/manifests/phase5_grouped_v3_s0_terminal01.json):
380 raw/2 remote hash khớp, 14 completed/recovered, 0 tool/guard requests;
22 graceful/2 terminate, 24 reaped. Không coi đây là utility/guard quality.
Quota sau shard 0 còn 28,23h; Dataset vẫn ready/v1. Chuẩn bị shards 1/2 theo lịch
đã chọn, không retry shard 0. Chưa có URL/version của hai job tiếp theo.

Kiểm tra đúng owner cho grouped package v3:
[live receipt](../experiments/manifests/phase5_grouped_package_v3_live01.json).
`huylmhuhu` còn 29,02/30h GPU, refresh 2026-09-19; Dataset
[guard15-probe-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
**private, ready, v1**; Qwen model instance v1 truy cập được. Source package
`0d86536`; [preflight](../experiments/manifests/phase5_grouped_package_v3_preflight01.json)
đã đạt; [full QA 3.113 pass/1 skip](../experiments/manifests/phase5_grouped_package_v3_cpu01.json)
đã chốt. Shard 0 đã submit như trên; bảy shard khác chưa có URL/version thực tế.
Không suy đoán notebook tồn tại/không tồn tại từ lỗi status của tên dự kiến.

Đính chính: snapshot quota và lỗi permission dưới đây được lấy bằng credential
mặc định, **không xác thực owner `huylmhuhu`**; không dùng chúng làm quota/quyền
của dự án. Chọn explicit owner từ credential project đã kiểm lại status notebook
document v1 thành công: **COMPLETE**. Không cần tài khoản hoặc quyền mới vì lỗi
403 trước đó. Quota đúng owner phải đọc live trước submission tiếp theo.

Nội dung lịch sử giữ lại (không phải gate quyền/quota hiện hành):

CLI dùng credential path của project, không in credential values. Quota live:
GPU used `0.09h`, remaining `29.91h`, total `30.00h`, refresh
`2026-09-19T00:00:00`; TPU remaining `20.00h`. Đây là snapshot tại thời điểm
audit, không phải reservation. Kiểm tra status notebook private
`huylmhuhu/react-vn-document-runtime-v1` trả permission denied; không đổi URL
hoặc suy đoán COMPLETE mới. Native grouped v2 chưa có notebook/Dataset URL hay
version thực tế; compile-only preflight vẫn ghi `native_submission_ready=false`.

## Phase 1/2 và pilot nhiều model

| Thực nghiệm | Notebook | Dataset | Bằng chứng |
|---|---|---|---|
| Phase 1 smoke | [phase-1-real-model-smoke](https://www.kaggle.com/code/huylmhuhu/react-vietnamese-agent-phase-1-real-model-smoke) v4 | [phase1-bundle](https://www.kaggle.com/datasets/huylmhuhu/react-vietnamese-agent-phase1-bundle) v5 | [Receipt](../experiments/manifests/phase1_kaggle_v4.json) |
| Phase 2 v1 cũ | [phase-2-clean-dev-pilot](https://www.kaggle.com/code/huylmhuhu/react-vietnamese-agent-phase-2-clean-dev-pilot) | [phase2-dev-bundle](https://www.kaggle.com/datasets/huylmhuhu/react-vietnamese-agent-phase2-dev-bundle) | [Receipt lịch sử](../experiments/manifests/phase2_kaggle_v2.json); không thay clean_v1.1 |
| Phase 2 clean_v1.1 | [vietnamese-clean-v1-1-dev-pilot](https://www.kaggle.com/code/huylmhuhu/react-vietnamese-clean-v1-1-dev-pilot) v1 | [clean-v11-dev](https://www.kaggle.com/datasets/huylmhuhu/react-vn-clean-v11-dev) v1 | [Receipt](../experiments/manifests/phase2_clean_v11_kaggle_v1.json); dùng **actual_kernel**, không alias tên yêu cầu |
| Gemma 4 measured Dev | [gemma4-measured-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-gemma4-measured-run-v1) v1 | [gemma4-measured-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-gemma4-measured-data-v1) | [Completion](../experiments/manifests/measured_pilot_completion.json), [submission](../experiments/manifests/measured_pilot_submission.json) |
| Qwen 7B measured Dev | [qwen7b-measured-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-qwen7b-measured-run-v1) v1 | [qwen7b-measured-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-qwen7b-measured-data-v1) | [Báo cáo measured Dev](../docs/evaluation/measured_dev_pilot_report.md) |

Llama chưa chạy tại mốc measured pilot vì thiếu quyền Meta; không có notebook
kết quả Llama để dẫn. Các alias/preflight draft không phải lượt được nghiệm thu
không được nâng thành kết quả chỉ vì tìm thấy handle trong source.

## Cách duy trì sổ

Sau mỗi submission thêm URL notebook, version, Dataset/version, source commit,
report/receipt và trạng thái có ngày kiểm. Sau terminal bổ sung raw path và giới
hạn; giữ riêng lỗi và lượt thay thế. Không ghi credentials/private GT/Test payload.
Chạy `make knowledge-check` sau sửa liên kết. URL ngoài repo được lưu từ receipts;
knowledge-check chỉ kiểm link local/cấu trúc, không xác nhận quyền mở trên Kaggle.

[Kaggle lessons](kaggle_lessons.md) · [Runbook](runbook.md) · [Handoff](handoff.md).
