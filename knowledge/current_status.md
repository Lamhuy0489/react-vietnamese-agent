# Trạng thái hiện tại

Cập nhật 2026-09-23. **Phase 5 đang làm: 4/7 ≈ 57% nhóm nghiệm thu**,
không phải phần trăm công sức hoặc số dòng mã. Phase 1–4 đã accepted theo
[trạng thái chính thức](../docs/project/phase_status.md); Test vẫn khóa.

## Kết quả mới nhất

**Dev32 v2 COMPLETE và audit độc lập, chưa chấm quality/utility.**
[Terminal report](../docs/evaluation/phase5_clause_dev_gpu_v2_terminal_report.md),
[selected receipt](../experiments/manifests/phase5_clause_dev_v2_gpu_terminal01.json).
Actual notebook version1/ID135499833, source `ad152ff`; 32/32 fixed public Dev,
8/8 shards, 2.073 raw/2 remote files và 222 source pins xác thực. Hai audits
và hai báo cáo mô tả có SHA khớp. 65/65 returned guard responses syntax `OK`;
8 ca không gọi guard, 31/32 graceful toàn bộ workers, một guard TERMINATE.
Không Test/private GT, không retry. ASR/FPR/benign utility và final semantics
chưa chấm; formal Phase5 vẫn 4/7≈57%. Bước tiếp: evaluator-only Dev scoring
trên raw bất biến, không chạy lại model.

Mốc trước — submission/RUNNING (quan sát lịch sử):

**Dev32 v2 đã submit một lần lên Kaggle; RUNNING lúc 09:55:43 UTC 2026-09-23.**
[Notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2)
v1/ID135499833, private/offline/T4, source commit `ad152ff8c8970df28cd6b5b0a0eebd02481b8e1e`.
[Release02](../experiments/manifests/phase5_clause_dev_package_v2_release02.json),
[submission](../experiments/manifests/phase5_clause_dev_v2_gpu_submission01.json).
Remote source/settings/version khớp; chưa có terminal output hoặc quality score.
Tiếp theo chỉ monitor read-only, khi terminal thì tải vào thư mục mới và audit
version/source trước-sau download; không submit trùng.

Mốc trước — v1 ERROR và chuẩn bị v2:

**Kaggle Dev32 v1 kết thúc ERROR trước worker đầu tiên; gói v2 đã qua QA.**
[Failure report](../docs/evaluation/phase5_clause_dev_gpu_v1_failure_report.md),
[v2 report](../docs/evaluation/phase5_clause_dev_package_v2_report.md),
[QA02](../experiments/manifests/phase5_clause_dev_package_v2_qa02.json).
V1/version1/ID135340687 source`5a23528` đã xác thực;0/32tasks hoàn tất,
0model-generation evidence. Lỗi `constrained` được truyền hai lần ở native path.
Raw, log và 12 files đã tải/lưu; hai failure audits khớp. Đã sửa riêng dispatch v2;
test tái hiện lỗi v1 và xác nhận v2 dùng constraint root của guard factory.
Development package hai layouts qua đủ 32 Dev và 21 Dummy; QA02 qua 980 focused,
395 integration, Ruff/mypy501/setup/knowledge. Kaggle read-only: GPU còn 29,73h,
Dataset guard15 private/ready/v1. Source freeze `24164d8` đã push main;
committed rehearsal release01 qua cả hai layouts nhưng host validator còn
allowlist cache v1, nên release01 bị từ chối, chưa submit. Sửa validator và
regression test đã qua QA03 (981 focused/395 integration/Ruff/mypy501/setup);
Cổng này đã đóng bằng release02/commit `ad152ff` ở trên.
Không resume v1 hay gửi lại cùng phiên bản. Phase5 vẫn 4/7≈57%, Test khóa.

Mốc trước — submission status lịch sử:

**Đã submit32Dev lên Kaggle một lần; RUNNING lúc07:10:42UTC ngày2026-09-22.**
[Notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v1),
v1/ID135340687,source`5a23528` đã pushmain;private/offline/T4/session14400s.
[Submission](../experiments/manifests/phase5_clause_dev_gpu_submission01.json),
[report](../docs/evaluation/phase5_clause_dev_package_v1_report.md).
Committed package hai layouts đạt,218source pins xác thực;remote code/settings/version khớp.
Đang chờ native kết quả32ca,không submit trùng. Tiếp theo terminal download và
source/version audit trước chấm chất lượng. Một commit source-freeze cần thiết;
không commit status tiếp. Formal4/7≈57% vẫn giữ,Test khóa.

Mốc trước — chuẩn bị release:

**Dev32 đã có exact package +source admission/launcher; development preflight đạt.**
[Report](../docs/evaluation/phase5_clause_dev_package_v1_report.md).
Hai layouts độc lập mỗi layout8tools/21Dummy/32Dev;211worker/218source pins.
QA976focused+395integration đạt,setup/Ruff/mypy495/knowledge/diff đạt.
Tiếp theo source freeze cần thiết,committed rehearsal/release audit rồi một lần
Kaggle32Dev. Live account/quota/privateDataset đã kiểm;chưa submit/model/GPU mới.
Giữ failures/checkpoints/Test;57% là formal acceptance, không số lượng code.

Mốc trước — CPU runner:

**Dev32 runner/checkpoint đã hoàn tất kiểm chứng CPU; chưa chạy model thật.**
[Report](../docs/evaluation/phase5_clause_dev32_v1_report.md),
[audit](../experiments/manifests/phase5_clause_dev32_audit01.json).
32/32ca A2/A6 từ16public Dev,8shards;64workers GRACEFUL/reaped,32synthetic recovery.
Complete-resume và hai audits/shard không đổi raw;188source/928raw pins khớp.
23tests mới; [QA](../experiments/manifests/phase5_clause_dev32_qa02.json):888focused+
395integration đạt; setup/Ruff/mypy488/knowledge/diff đạt,182native/169data pins nguyên.
Đã có native artifact/token-count audit adapter, nhưng chưa xác thực native release;
HF runner vẫn khóa. Tiếp theo native source/release gate +launcher +exact package
rehearsal, rồi source freeze cần thiết và32Dev Kaggle. Không thêm4task diagnostic.
Không Test/private GT parsing, GPU/commit/push mới;57% acceptance giữ nguyên.

Mốc trước — nền paired integration:

**V12 + constrained ExitPair đã tích hợp và qua CPU gate.**
[Report](../docs/evaluation/phase5_clause_pair_v1_report.md),
[receipt](../experiments/manifests/phase5_clause_pair_controls01.json).
12tasks/24workers reaped:4completed +4lỗi chủ động giữ nguyên +4egress controls đúng.
20GRACEFUL/4TERMINATE, forced chỉ trong failure controls; chưa native reliability.
Audit tái dựng raw authority/origin, resume không chạy lại terminal;184source/
348raw hashes khớp, scan349files/0credentials.36new tests đạt.
[Final QA](../experiments/manifests/phase5_clause_pair_qa01.json):879focused+
381integration đạt; setup/Ruff/mypy483/knowledge/diff đạt;182native pins và169data
hashes nguyên. Full pytest loại sealed Test-authoring fixtures.
Tiếp theo32Dev runner/native release audit vàexact package, rồi mới khóa source/GPU.
Không pending Kaggle, không model lớn/commit/push mới;57% vẫn theo acceptance.

Mốc trước — candidate chưa qua paired path khi ghi mốc này:

**V12 cumulative + clause anchors v3: 78/78 CPU controls đạt.**
[Report](../docs/evaluation/phase5_clause_candidate_v1_report.md),
[receipt](../experiments/manifests/phase5_clause_candidate01.json).
Đã nối cùng parser quyền gửi ở A1–A6, A0 delegate v10; bảo toàn các veto và
kiểm tra final. Bổ sung nguồn gốc literal đích gửi từ raw host-user để sửa lỗi
email trước dấu chấm. Sáu Dev destination gaps đã đóng ở mức parser, không
đồng nghĩa payload CONFIDENTIAL được phép gửi hay benchmark utility đạt.
67 targeted unit +65 integration đạt; raw1.400/source157 pins kiểm riêng,
scan1.401files/0credential matches.
[Final QA](../experiments/manifests/phase5_clause_qa01.json):873focused+
351integration đạt; setup/Ruff/mypy478/knowledge/diff đạt;182native pins và
169tracked data hashes không đổi. Full pytest loại Test-authoring fixtures.
Tiếp theo nối constrained ExitPair/native + independent audits, exact package,
rồi workload32caA2/A6. Chưa GPU/commit/push; không job pending;57% chưa đổi.

Mốc trước, không phải candidate hiện hành:

**Đã có coverage16ca Dev/8cặp và đối chứng lỗi quyền gửi.**
[Report](../docs/evaluation/phase5_acceptance_controls_v1_report.md).
v10:26/26dạng `;` đạt nhưng chỉ17/26dạng dấu chấm,9ca bị chặn sai. Ứng viên
anchorv2/runtimev11 A6 CPU:52/52đạt, vẫn giữ sensitive/unknown/veto/final protections.
Chưa production/native/cumulative rollout;6fixtures Dev có anchor thiếu chưa
được coi đã sửa. Raw/source pins kiểm riêng,scan1868files/0credentials.
Final QA806focused+286integration, setup/Ruff/mypy474/knowledge/diff đạt;
182native source pins không đổi.
Tiếp theo clause-scoped quyền/cấm, parity các mức và native integration rồi mới
gửi workload32ca A2/A6 đã định trước. Không commit/push/GPU mới;57% chưa đổi.

**ExitPair GPU v1 COMPLETE/audit, post-download07:28:29UTC ngày2026-09-21.**
[Report](../docs/evaluation/phase5_exit_gpu_v1_report.md),
[summary](../experiments/manifests/phase5_exit_gpu_summary01.json).
4/4 completed,8/8 valid guard responses,8GRACEFUL/0TERMINATE/0KILL,4VRAM recoveries.
Tất cả exit stages return; không tái hiện lỗi teardown cũ, chưa root cause/fix.
Hai release audits khớp:182source/242raw/2remote;scan253files/0credentials.
Final QA773focused +180integration, setup/Ruff/mypy468/knowledge/diff đạt.
Actual notebook/version/source không đổi. Không pending job hoặc submit mới.
Tiếp theo coverage matrix public Dev cho representative guard quality/benign
utility; lifecycle reliability vẫn mở. Không commit/push lượt audit này.

Mốc submit lịch sử:

**ExitPair GPU v1 đã chạy trên Kaggle; RUNNING lúc 16:57:50 UTC ngày 2026-09-20.**
[Report](../docs/evaluation/phase5_exit_pair_package_v1_report.md),
[submission](../experiments/manifests/phase5_exit_gpu_submission01.json).
Actual `huylmhuhu/react-vn-exit-milestones-v1`, v1/ID135130970; private/offline/T4,
timeout3600s, source `6d039e2` đã push main, code/settings/version remote khớp.
Development + committed package đều qua hai layouts:176worker/182source pins;
final QA763focused+180integration, setup/Ruff/mypy467/knowledge đạt.
Một commit nguồn và một lần submit; không status-only commit. Chờ terminal để
tải/kiểm toán output; chưa native cause/fix hay tăng acceptance. Các đoạn dưới
là mốc lịch sử, không dùng các câu “chưa job” cũ làm trạng thái hiện tại.

**ExitPair/runner và native audit wiring đã triển khai local.**
[Report](../docs/evaluation/phase5_exit_pair_cpu_v1_report.md).
Role/task/PID/cold-warm config được nối qua sidecar riêng, frozen worker không đổi.
54 tests mới đạt; final QA02 689 focused + 180 integration,
setup/Ruff/mypy462/knowledge/diff đạt. Controls02 gồm 4 completed + 4 deliberate model_error,
16 worker reaped; audits trước/sau complete-resume khớp. Native composition tests
là mock/lazy, chưa pretrained execution hay package. Cross-environment audit dùng
interpreter trong run identity, không nhầm với OS/Python của máy đang kiểm toán.
Không commit/push: owner nhắc lại giữ local, QA đạt không tự động tạo commit.
Tiếp theo là exact notebook/package và release authentication trước GPU.

Nền observer đã đóng:

**Opt-in exit milestones đã đạt CPU acceptance.**
[Report](../docs/evaluation/phase5_exit_milestones_cpu_v1_report.md),
[close receipt](../experiments/manifests/phase5_exit_milestones_cpu_close01.json).
18/18 worker reaped, 6 GRACEFUL/9 TERMINATE/3 KILL; responses và normalized attempts
khớp đối chứng cũ. Dấu mốc mới tách target chưa return, exit finalizers bị kẹt,
và thread shutdown bị kẹt. Không phải native GPU root-cause/fix.
Hai audits byte-identical; 53 tests mới, final QA 666 focused + 149 integration,
setup/Ruff/mypy454/knowledge đạt; 172/142/86/175 frozen pins không đổi.
Chưa có job Kaggle mới. Bước tiếp theo: native runner/receipt join và exact package
riêng, giữ worker cũ và grace2s; không tăng acceptance chỉ từ CPU controls.

Mốc tổ chức tri thức:

Đã thêm [trang bắt đầu](../START_HERE.md) và
[quy ước lưu trữ/Obsidian](storage_and_obsidian.md): dùng lại Markdown hiện có,
không tạo memory song song; settings/trash của vault ngoài Git. Không đổi cấu hình
Obsidian, không bật sync/plugin hoặc sao lưu raw ra ngoài máy. Việc tổ chức ghi
chú không tăng acceptance.

**CPU post-serve teardown controls đã hoàn tất: 18/18 worker được thu hồi.**
[Report](../docs/evaluation/phase5_teardown_cpu_v1_report.md),
[receipt](../experiments/manifests/phase5_teardown_cpu_close01.json).
6 cơ chế × 3 lần, giữ grace2s: 6 GRACEFUL/9 TERMINATE/3 KILL đúng các đối chứng
đã định trước. Finalizer bị kẹt và non-daemon thread còn sống đều có thể tạo
serve-returned + forced exit; chưa xác định cơ chế thật trên GPU.
Hai audits byte-identical, 44 tests mới; final QA 623 focused + 133 integration,
setup/Ruff/mypy450/knowledge đạt. Giữ nguyên 172/142/86/175 source pins.
Không dùng GPU, không submit lại notebook. Tiếp theo là native exit-milestone
instrumentation riêng, chưa tăng deadline hoặc sửa model/prompt.

Mốc native trước:

**Constrained guard GPU v1 COMPLETE; hai release audits khớp byte-for-byte.**
[Report](../docs/evaluation/phase5_constrained_gpu_v1_report.md),
[submission](../experiments/manifests/phase5_constrained_gpu_submission02.json).
Actual `huylmhuhu/react-vn-constrained-guard-v1`, version 1/ID 134673914;
private/offline/T4, source `0d4e82f` khớp remote, guard Dataset v1.
Post-download check 03:43:34 UTC ngày 2026-09-17 vẫn COMPLETE/v1/private.
[Summary](../experiments/manifests/phase5_constrained_gpu_summary01.json):
4/4 tasks completed, 8/8 guard responses valid (4 PRE/4 POST), 0 incomplete
constraints/backend errors; 8 workers reaped/4 VRAM recoveries.
**Còn 4 TERMINATE/4 GRACEFUL**; chưa lifecycle acceptance. 172 source/238 raw/2 remote
files authenticated; scan 256 files/0 credential matches. Không còn job pending,
không submit lại. Đây là syntax/integration evidence, chưa guard quality/utility.
Host auditor/summary có 64 tests mới. [Final QA](../experiments/manifests/phase5_constrained_release_cpu_qa02.json):
573 focused + 105 integration tests; setup/Ruff/mypy446/knowledge đạt.
Gom host code/tests/evidence/memory trong một commit sau khi thực nghiệm đóng;
không amend source worker hoặc commit lẻ mỗi status.

Nền package đã đóng:

**Constrained notebook/bootstrap và exact package đã đạt cả development và committed rehearsal.**
[Report](../docs/evaluation/phase5_constrained_package_v1_report.md),
[receipt](../experiments/manifests/phase5_constrained_probe_package_dev01.json).
166 file worker/172 source pins; archive và expanded đều đạt 8 tools,
21 Dummy, valid/failure controls và immutable/missing-only resume trong venv
offline mới. Không load model/GPU. Bản development bị chặn native execution;
source-freeze `0d4e82f` đã push `main`; committed package01 chạy lại hai layout đạt.
[Release receipt](../experiments/manifests/phase5_constrained_probe_package01.json).
Terminal remote authentication đã đạt. Biên bản sau freeze được gộp với host
auditor/report khi đóng thực nghiệm, không thêm status-only commit.
Final QA: 495 focused + 105 integration tests, setup/Ruff/mypy444/knowledge đạt;
142/86/175 frozen source pins nguyên.
Đã cập nhật hai skill dự án: gom việc hoàn chỉnh/QA/memory, không commit lẻ từng
trạng thái; freeze source cần thiết cho thực nghiệm là ngoại lệ giải thích trước.

Nền runner đã đóng:

**Runner/checkpoint và native-auditor join đã nối xong, QA đạt.**
[Report](../docs/evaluation/phase5_constrained_probe_v1_report.md).
32 tests mới qua; controls02 có 4 completed/4 lỗi chủ động được giữ nguyên,
resume không chạy lại ca terminal. Đây là synthetic CPU, chưa gói Kaggle/GPU.
480 focused + 105 integration tests đạt; setup/Ruff/mypy443/knowledge đạt.
142 active + 86 prior-native + 175 baseline source pins nguyên.
Pre-commit working-tree source hashes được lưu; gom một commit sau khi QA đạt.

Nền host/runtime trước:

**Host classifier/cache đã nối với paired runtime và read-only auditor riêng.**
[Report](../docs/evaluation/phase5_constrained_host_v1_report.md), source `e04cd8d`.
37 tests mới qua, gồm spawned CALC/DOC × A2/A6, cache không thêm IPC, lỗi worker,
đổi identity và thay receipt bị chặn. Đây là synthetic CPU, chưa production guard.
Final QA: 438 focused + 90 integration tests đạt; setup/Ruff/mypy437/knowledge đạt.
142 active + 86 prior-native + 175 baseline source pins nguyên. Không có GPU job mới.

Mốc native CPU trước, giữ nguyên:

**Native constrained-generation CPU v2 COMPLETE và audit đạt.**
[Report và bằng chứng](../docs/evaluation/phase5_constrained_generate_cpu_v2_run.md).
Notebook `huylmhuhu/react-vn-constrained-generate-cpu-v2`, version 1/ID 134579648,
source `b4ae0f7`; sau download xác minh COMPLETE/private/source khớp lúc
2026-09-16 08:25:13 UTC. Không còn job pending trong lịch CPU này.

Hai ca sinh thật trên tiny random Qwen đều hoàn tất JSON + EOS, mỗi ca 28 token;
0,2362s và 0,1462s. ForcedBOS bị từ chối trước forward; interrupt truyền ra và
khôi phục hook. Cả bốn ca khôi phục đúng; không pretrained weights/GPU/quality.
Hai audits byte-identical: 142 source pins, 25 raw và 2 remote files xác minh.
401 focused tests đạt / 21,87s; setup/Ruff/mypy 433/knowledge đạt.
22 tests mới kiểm auditor. Không full pytest vì có Test-assigned authoring fixtures.

CPU v1 ERROR và sáu lỗi int/float trong policy pin được giữ nguyên lịch sử,
không thay thất bại cũ bằng v2. V2 chỉ sửa expected typed policy identity,
không đổi numerical decoding/prompt/model/parser.

## Việc đang nối tiếp

Worker composition và host classifier/cache/runtime join đã có CPU tests.
Native wrapper đã nối constraint với policy/attention/HF metrics và runner có
checkpoint identity riêng. Notebook/bootstrap đã qua development exact rehearsal.
Committed release preflight và GPU v1 terminal/release authentication đã đạt.
**CPU controlled teardown đã đạt; bước tiếp là native exit-milestone diagnostic**,
rồi đại diện
guard quality/benign utility và mapping 20 DoD. Native v1 chứng minh 8 phản hồi
đúng syntax trong 4 ca, không thay thế chất lượng phân loại hay graceful lifecycle.

Giữ baseline 175 source pins, native tokenizer 86 pins và package CPU 142 pins.
Không submit lại bare-json-v2, CPU v1/v2 hoặc retry semantic failures.
Không chuyển Phase 6/7 hoặc mở Test. Không cần tài khoản mới lúc này.

## Nền đã đóng

- Grouped native: đủ 112/112 ca đã audit; 82 completed/30 model_error,
  55 valid/30 malformed guard responses; 192 workers reaped, còn 13 forced shutdowns.
  [Báo cáo tổng](../docs/evaluation/phase5_grouped_v3_complete_report.md).
- Bare-JSON: 4 model_error, 2/6 valid guard responses; prompt-only chưa khắc phục.
  [Kết quả âm](../docs/evaluation/phase5_guard_bare_json_terminal_v1.md).
- Tokenizer native: 3069 values, max 36 tokens gồm EOS, 248 mask checks.
  [Nền CPU](../docs/evaluation/phase5_guard_language_native_v1_run.md).
- [SQL scope](sql_scope_v5.md), [public resource scope](resource_scope_v4.md),
  [grouped runner](grouped_runner_v1.md) giữ nguyên.

[Bàn giao](handoff.md) · [DoD còn thiếu](phase5_remaining.md) ·
[Sổ notebook/Dataset](kaggle_resources.md) · [Chỉ mục](README.md).
[Lịch sử trước mốc CPU v2](history_20260916_constrained_cpu.md) giữ nguyên;
các câu “đang chạy/chuẩn bị” trong lịch sử không phải trạng thái hiện tại.
