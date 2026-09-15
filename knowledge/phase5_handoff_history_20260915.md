# Lịch sử bàn giao trước khi đóng bare-JSON candidate

Không dùng chỉ dẫn RUNNING/submit trong bản lưu này làm bước tiếp hiện hành.
Xem [bàn giao hiện hành](handoff.md).

# Bàn giao phiên làm việc

Cập nhật: 2026-09-15. Chỉ dẫn hiện hành; lịch sử không thay thế mục này.

## Đang làm

**Việc hiện hành: terminalaudit observer native v2 đã đóng**, kiểm11:52:53UTC,
ID134481763; [report/links/receipts](../docs/evaluation/phase5_observer_native_v2_run.md).
Source`c0930bf`, actual `huylmhuhu/react-vn-observer-native-v2`, mã tải ngược khớp,
private/offlineT4x2/14400s, v1COMPLETE trước/sau download.4model_error,4toolcalls,
6guardresponses(2valid/4fenced syntax),2POST backendfailures không response.
8workersreaped/4VRAMrecoveries nhưng3TERMINATE; tất cả3đã ACK và serve-return.
Hai releaseaudits/summaryJSON/CSV byte-identical;159source/158raw/2remote verified.
Raw đóng: `results/phase5_observer_native_v2_terminal02`; reports01/02 và
terminal_qa01 theo cùng prefix.67focused tests/setup/Ruff/mypy409 đạt.
182files scan/0credentials,175baseline pins nguyên; knowledge-check sau selection
đạt ([receipt](../experiments/manifests/phase5_observer_native_v2_close01.json)).
Reporter mới tự releaseaudit trước thống kê; không chạy downloaded source.
Không full pytest vì Test-assigned authoring fixtures; không mới model/Test/GT.

**Bước tiếp cụ thể:** làm candidate prompt-only bareJSON/noMarkdown trong version
riêng, giữ parser/schema/model/generation/fallback. CPU tests phải kiểm prompt/cache
identity, strict rejection, retirement và untrusted-input isolation; sau đó khóa
protocol mới, exact package preflight, GitHub rồi Kaggle riêng. Chưa triển khai
candidate này. Khảo sát shutdown sau serve-return bằng synthetic controls riêng,
không gộp đổi timeout vào thí nghiệm prompt. [Queue DoD](phase5_remaining.md).
Giữ mọi lỗi4ca/112baseline; không resubmit helper, ghi đè outputs hoặc sửa159pins.
Pending access: không cần tài khoản mới; phải live check quota/private mounts
trước GPUjob mới. Các câu“RUNNING/chưa submit”dưới đây là lịch sử.

Candidate đã có source `f7492fa`, CPU preflight01 đạt ở archive/expanded với
8tools/21cleanDummy/4task×3conditions và missing-only resume; [receipt/report](../docs/evaluation/phase5_guard_bare_json_preflight_v1.md).
Access01 lúc2026-09-15: owner `huylmhuhu`, GPU còn22.80h, Datasetguard15 ready/v1.
Gói `build/kaggle/phase5_guard_bare_json_package_v1_preflight01` đủ điều kiện
cho **một** notebook private mới. Nếu submit: dùng actual handle mới, verify
version/source rồi download/audit hai lượt; không submit lại baseline/candidate.
Đã thực hiện submit đúng một lần: actual `huylmhuhu/react-vn-guard-bare-json-v1`,
v1/ID134511636, receipt ghi RUNNING và source hash khớp. Bước hiện tại là verify
terminal, tải output mới và audit; không gửi version thứ hai.

**Observer native đã sẵn sàng gửi:** source `c0930bf`, notebook và native audit
cho4tasks;53focused checks/setup/Ruff/mypy407 đạt, helper đối chiếu logGPU cũ đạt.
Preflight03 hai layouts bằng source nhúng đã đạt66.21s:153packagefiles,
159source pins/706raw kiểm lại;175baseline pins nguyên. [Receipt](../experiments/manifests/phase5_observer_package_v2_cpu03.json).
Requested handle `huylmhuhu/react-vn-observer-native-v2`; chưa submit tại mốc này.
Access01:23.08hGPU, Datasetready/v1. Sau push source/evidence lênGitHub, gửi một
lần từ `build/kaggle/phase5_observer_package_v2_preflight03/kernel`, private/offline
T4x2/14400s, rồi verifyactualhandle/version/source và cập nhậtKaggle directory.
Owner đã cho phép workflow. Những mục“thiếu notebook/auditor”bên dưới là lịch sử.

**Hiện hành: gói observer v2 CPU preflight02 đã đạt**, source `ed0f6db`.
[Report/receipts](../docs/evaluation/phase5_observer_package_v2_report.md).
Hai layouts/fresh venv: mỗi layout8tools/21cleanDummy và4observer tasks×2conditions,
missing-only resume đạt.706raw/145source hashes kiểm lại,175worker pins nguyên.
99focused tests(41.02s)/setup/Ruff/mypy405/knowledge đạt; preflight67.31s.
Raw/package: `build/kaggle/phase5_observer_package_v2_preflight02`;
log: `results/phase5_observer_package_v2_preflight02`. Giữ preflight01 thất bại.
HF factory regression kiểm đúng thứ tự tạo metricsdir; runner khóa6sourcehashes,
kiểm toàn bộ checkpoint trước resume. Audit nhận commit tường minh.
Hai probe `valid01`/`malformed01` cũ có historical re-audit; baseHEAD cũ không
chứa code workingtree lúc chạy, không được nâng thành chứng cứ source-pinned.

**Bước tiếp cụ thể:** thêm native metrics/source audit cho lịch4tasks, ghép
tokenizer/publisher/attention/policy và worker/host response/lifecycle/GPU memory;
khóa notebook launcher dùng runner đã chuẩn bị, chạy package preflight mới sau
khi thêm source, rồi kiểm quota/Dataset/model mounts để submit. Owner đã cho
phép workflow Kaggle/GitHub; không cần hỏi lại ý định. Chưa có native launch
hayGPUjob; `native_submission_ready=false` là tình trạng kỹ thuật của gói.
Không ghi đè output/identity đã đóng; không chạy lại helper preflight01/02.

Các đoạn bên dưới ghi lại các mốc đã hoàn tất trước preflight02.

**Lịch native112/112 đã terminal/audit; không submit/rerun hoặc tải lại.**
[Report tổng](../docs/evaluation/phase5_grouped_v3_complete_report.md),
[summary/CSV/QA](../experiments/manifests/phase5_grouped_v3_suite01.json),
[follow-up](../docs/evaluation/phase5_post_native_actions_v1.md).
82completed/30model_error,55valid/30invalid guard responses+18backend failures;
192reaped(179graceful/13terminate),112recovered. Guard quality/semantic utility/
uniform graceful shutdown chưa đạt; Phase5vẫn4/7≈57%. Không cóGPUjobpending.
ROWLIST COMPLETE05:53:41UTC/v1, source/version xác minh;614raw/2remote khớp.
Suite reporter re-audit8shards/fullrunidentity/112uniquekeys; hai outputJSON/CSV
byte-identical.59focused/setup/Ruff/mypy395/knowledge đạt; scan4332files sạch.
Raw outputs đã đóng. **Observer/join diagnostic v2 CPU đã xong**:
worker sidecar + host witness hash độc lập;139focused checks/setup/Ruff/mypy399.
A2–A6 CPU spawn/parity/retirement và mutations đạt; không đổi175worker pins.
[Memory/QA/contract](guard_diagnostics_v2.md). Raw QA/process fixtures giữ tại
`results/phase5_guard_observer_v2_cpu01`, không ghi đè hoặc chạy lại helper cùng output.
Bước mới: khóa synthetic native diagnostic protocol/expected calls, ghép opt-in
factory riêng và exact isolated package preflight. Chưa native wiring/package/
inference; không sửa frozen parser/prompt/model hay thu raw guard text.
Host witness không tồn tại trong baseline cũ; không suy đoán raw30lỗi từ enum/hash.
Không có access pending ở mốc CPU; cần kiểm quota/mount/model access khi chuẩn bị GPU.

**Đã hoàn tất mốc protocol/probe CPU:** [contract](../docs/architecture/phase5_observer_native_v2_contract.md),
runner/auditor `scripts/run_phase5_guard_observer_v2.py` và
`scripts/audit_phase5_guard_observer_probe_v2.py`; valid 4/4, malformed 0/4,
8/4 guard responses tương ứng, PRE/POST và recovery đều đúng. Raw:
`results/phase5_guard_observer_probe_v2_valid01`,
`results/phase5_guard_observer_probe_v2_malformed01`; audit:
`experiments/manifests/phase5_guard_observer_probe_v2_cpu01.json`.
Commit tiếp theo phải giữ nguyên hai raw probe; exact package preflight là bước
cụ thể kế tiếp. Chưa gửi Kaggle/GPU và chưa cập nhật Phase5 acceptance.

Các mục dưới là lịch sử trước khi đóng lịch; không thực hiện chỉ dẫn submit cũ.

**Việc tiếp tục ngay: theo dõi shard7 ROWLIST R3 v1 RUNNING, không gửi lại.**
[Admission report/receipt](../docs/evaluation/phase5_grouped_v3_s7_admission_report.md).
Actual `huylmhuhu/react-vn-grouped-dev-v3-rowlist-r3`, kernel ID134443063,
v1RUNNING lúc2026-09-15 05:06:57UTC, failureMessage=null. Source/metadata tải
ngược khớp; GitHub evidence875399d trước push. [Submission03](../experiments/manifests/phase5_grouped_v3_s7_submission03.json).
Attempt01 bị giới hạn2GPU/02HTTP409 được giữ nguyên; không dùng địa chỉ cũ.
Launcher03 chỉ đổi id/title, wrapper/source nguyên khóa. Không chạy helper
submit cũ hoặc ghi đè outputs; cả112ca đã gửi,14ca cuối đang chờ kết quả.
Khi terminal: verifyversion/tải fresh output/releaseaudit hai lần bằng
submission03, summary/scan/timing/lifecycle. Không tự thêm ROWLIST column grants.

**Shards5 QUERYLEAK / 6 QUOTED v1 COMPLETE/audit**, kiểm2026-09-15 04:51UTC.
IDs134393202/134393213;502+662raw/4remote hashes khớp, scan1168files/0credentials.
Hai audits/shard byte-identical. QUERYLEAK4completed/10model_error; QUOTED14
completed/20valid PRE/POST. Tổng98/112audited(87,5%),68completed/30model_error.
[Report, actual URLs, receipts và raw paths](../docs/evaluation/phase5_grouped_v3_batch56_report.md).
Source `0d86536`, GitHub evidence `80a8bae` đã push; 175source và kernel pins
khớp, mã tải ngược xác thực. Dataset private ready/v1, quota trước gửi25,34h;
offline T4x2/14.400s. Raw/summary đã đóng, không tải/rerun trùng; xem report.
49focused tests/setup/Ruff/mypy394 đạt; full worker QA không chạy lại.
Chỉ còn14caROWLIST trong lịch native; Phase5 vẫn4/7≈57%, chưa quality/freeze.

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

**Chỉ dẫn hiện hành:** làm observer/join CPU cho diagnostic v2 ở đầu trang, giữ baseline
112ca bất biến. Các bước native bên dưới đã hoàn tất và chỉ là lịch sử.

Native v2 source `3486dbf` đã ghép. **Thu hồi kết luận package/import isolation**
của hai receipt cũ: overlay nằm dưới `configs`, editable install đã cung cấp
module từ repo. Giữ nguyên raw/receipt. Xem phần đính chính trong báo cáo native.
Package v3 preflight đã đạt; 14 regression tests đạt, Ruff/mypy392 đạt trước freeze.
Trạng thái native mới nhất ở đầu trang:0–6audited;7ROWLIST R3 v1RUNNING.

1. CPU QA và preflight đã hoàn tất; không chạy lại. Selected QA receipt đính chính
   scope Test của full historical suite, không coi flag cũ là filesystem audit.
2. Shards0–6 terminal/audit; raw/summaries đã đóng. Shard7R3đangRUNNING,
   kiểm terminal/tải mới/audit, không gửi lại hoặc dùng hai địa chỉ lỗi.
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
