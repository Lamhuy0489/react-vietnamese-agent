# Bàn giao phiên làm việc

Cập nhật: 2026-09-14. Chỉ dẫn hiện hành; các mốc v1/v6 là lịch sử, không thay thế mục này.

## Đang làm

**Ưu tiên hiện tại:** [resource scope v4/runtime v9](resource_scope_v4.md).
Host resource index, public Dev catalog, scope và pair adapter đã triển khai;
đang chốt tests và full CPU QA trước push. Output dự kiến
`results/phase5_resource_scope_v4_cpu01`, receipt cùng tên trong manifests.
Giữ raw/receipt cũ immutable. Bước kế sau QA là bounded SQL row scope, rồi Dev
runner/input identity/exact package và mới submit Kaggle. Không cần account mới,
không GPU job, không Test/private oracle. Các mốc bên dưới đã kết thúc.

**Đã chốt:** [guard diagnostics v1](guard_diagnostics_v1.md).
CPU01 đã đạt full2.871pass/1skip/714,93s; source `284590d`, 510source/424raw hashes
khớp, 169data unchanged; 40runtime receipts/25sidecars. Dev schedule metadata
đã chốt. Native factory/independent auditor source `c7fa18c` đã đạt full
**2.888pass/1skip/785,14s**, 75focused/64,83s; setup/Ruff/mypy365/knowledge đạt.
515source/567raw/169data hashes kiểm lại khớp, 51 actual runtime receipts.
[Native CPU receipt](../experiments/manifests/phase5_native_diagnostics_v1_cpu01.json)
SHA-256 `1ae96fa272782a174d94687ce9c808fc3ab88830023c915a61d2969662b2f994`.
Output `results/phase5_native_diagnostics_v1_cpu01` đã đóng; không chạy trùng/
ghi thêm. Không còn QA chạy. Bước kế ghép runner Dev với input/catalog manifest,
bounded scope rồi exact package. Pending access không cần tài khoản mới;
chưa có GPU job mới và chưa chứng nhận observer chạy native GPU.

**Đã kết thúc:** [document diagnostic v1](document_diagnostic_v1.md).
CPU draft01 phát hiện A4–A6 chặn CDOC; scope v3/runtime v8 sửa namespace có giới
hạn, giữ v7 frozen. Source `54aa3ec`. Full **2.813 pass/1 skip**, 693,77s;
49 focused/7,25s, setup/Ruff/mypy 357 files/knowledge đạt. CPU01 có 501 source/
158 raw hashes khớp, 169 data unchanged; exact preflight01 có 110 source/430 raw
hashes khớp. [CPU receipt](../experiments/manifests/phase5_document_probe_v1_cpu01.json),
[preflight](../experiments/manifests/phase5_document_probe_v1_preflight01.json).
Hai output01 đã xong, không chạy trùng/ghi thêm. GitHub đã push `8836e9c`.
**Đã submit notebook `huylmhuhu/react-vn-document-runtime-v1` version 1**,
T4/7200s/private/offline; [submission](../experiments/manifests/phase5_document_gpu_v1_submission01.json).
**Version1 COMPLETE/artifact audit đạt**, [receipt](../experiments/manifests/phase5_document_gpu_v1_audit01.json)
SHA-256 `ea799c3c1ab4afe8d2efa48be651241bd5f02686043c4caa7b3171f58a470228`.
261raw/2remote khớp; 7doc reads, A0/A1 completed, A2–A6 model_error. PRE guard
INVALID_OUTPUT dẫn tới retire đóng cả pair; POST không có native attempt.
8GRACEFUL/4TERMINATE, 12reaped; 7recovered/42samples/zero residual2GPU.
Raw `results/phase5_document_gpu_v1_output01`, remote `...remote01` đã đóng;
không còn job/downloader, không ghi thêm/retry semantic. Link trong [sổ Kaggle](kaggle_resources.md).
Bước kế: CPU synthetic INVALID_OUTPUT/fallback/retirement causal audit và
sanitized parser-error diagnostics, rồi prereg grouped Dev guard quality.
Không biết field JSON cụ thể vì loader không lưu raw guard output; không đoán.
Pending access: không cần tài khoản mới, kiểm live Dataset/private mounts/quota
owner huylmhuhu đã kiểm live Dataset ready/private/v1 và model listing ngày
2026-09-14; quota còn 29,43h tại snapshot, không reservation. Local không load model.
Các mốc bên dưới đã xong; cue `cho biết` không tạo scope anchor là limitation
đã ghi riêng, không kết luận authorization quality từ diagnostic này.

Đã chốt [shutdown package v2](shutdown_package_v2.md): wrapper/builder/release auditor
riêng và package checkpoint check, source `fa28401`; 24 focused tests đạt 7,11s.
Exact archive/expanded preflight01 đạt, 101 source/430 raw hashes khớp; receipt
đã lưu trong manifests. Full **2.764 pass/1 optional-tqdm skip**, 693,35s; setup/
Ruff/mypy 346 files/knowledge đạt. 485 source/137 raw hashes CPU khớp, 169 data
hashes không đổi. [Report](../docs/evaluation/phase5_shutdown_package_v2_report.md),
[CPU receipt](../experiments/manifests/phase5_shutdown_package_v2_cpu01.json) và
[preflight receipt](../experiments/manifests/phase5_shutdown_package_v2_preflight01.json).
CPU SHA-256 `1802c3c635c6cf431540afd2046d779eba6dfc290d93bcb4f7c256dc506d7e7d`;
preflight SHA-256 `b768d70b934e5aea4bced61a9dbfeac07303b8862c43a9bf92d91c363e184e45`.
Output `results/phase5_shutdown_package_v2_cpu01` và
`build/kaggle/phase5_shutdown_package_v2_preflight01` đã chốt; không ghi thêm/
chạy trùng. Không còn QA hoặc GPU job mới. Native submission chưa sẵn sàng:
calculator chỉ là CPU control, cần diagnostic mới định trước.

Đã chốt CPU [native shutdown wiring v2](native_shutdown_wiring_v2.md), source
`dfbd54f`: factory/runner/auditor riêng; 36 focused tests (27,70s), full
**2.740 pass/1 optional-tqdm skip**, 719,76s. Setup/Ruff/mypy 342 files/knowledge
đạt. 478 source/4.726 raw hashes khớp, 169 data hashes không đổi; 15 actual runtime
receipts, 70 native-shaped mocked records tách riêng. [Report](../docs/evaluation/phase5_native_shutdown_wiring_v2_report.md)
và [receipt](../experiments/manifests/phase5_native_shutdown_wiring_v2_cpu01.json),
SHA-256 `fd4c7a3fcc773811545a286d5b23e3b1bfa214526ba115bd54eb3052c1a8e911`.
Output `results/phase5_native_shutdown_wiring_v2_cpu01` đã chốt, không ghi thêm/
chạy trùng; mốc này đã xong. Package v2 phía trên nối tiếp; chưa GPU mới,
calculator chỉ là CPU control, không retry v1.

Đã chốt CPU [pair/runtime v3](pair_runtime_v3.md): cả agent-only và pair dùng observed
shutdown v2, A0/A1 tách start/call deadline; auditor nối PID/config/lifecycle.
Source `c4afb83`, 74 focused tests đạt 76,90s; 63 receipts đã join độc lập.
Full QA **2.704 pass/1 optional-tqdm skip**, 670,56s; setup/Ruff/mypy 335 files/
knowledge đạt. 468 source/646 raw hashes khớp, 169 data hashes không đổi.
[Receipt](../experiments/manifests/phase5_pair_runtime_v3_cpu01.json) SHA-256
`fc86feb846340e8e323e6f5fc842ab0f977f49463853decdbe2e3ba94aa183d8`;
[report](../docs/evaluation/phase5_pair_runtime_v3_report.md). Không còn QA chạy;
chưa có GPU mới. Output `results/phase5_pair_runtime_v3_cpu01` đã chốt,
không chạy trùng/ghi thêm. Mốc CPU v3 này đã kết thúc; wiring v2 đạt CPU phía trên.

Sổ tài nguyên cho nhóm: [Kaggle notebook/Dataset links](kaggle_resources.md),
gồm mốc hiện hành/lịch sử, version, receipts và lưu ý quyền private. Tiếp phần
exact package sau CPU wiring; chưa gửi GPU hoặc đọc Test mới.

[Worker shutdown v2](worker_shutdown_v2.md) là mốc standalone CPU trước: 80 focused
tests đạt (34 mới + 46 cũ), 8 v2 events + một legacy control; chưa tích hợp
ModelPair/native ở mốc đó. Full QA **2.630 pass/1 optional-tqdm skip**, 581,50s;
setup/Ruff/mypy 331 files/knowledge đạt. Source `a45696b`, output riêng
`results/phase5_worker_shutdown_v2_cpu01`; [receipt](../experiments/manifests/phase5_worker_shutdown_v2_cpu01.json).
462 source/677 raw hashes kiểm lại khớp, 169 data hashes không đổi. Job mốc
standalone đã xong. [Report](../docs/evaluation/phase5_worker_shutdown_v2_report.md).
Đã kiểm riêng 26 Kaggle handles trong directory đều có manifest đã lưu; không
phải live access check. README/AGENTS liên kết và quy định cập nhật directory.

Đang làm [seven-level runtime package](phase5_security_runtime_probe_v1.md):
agent-only factory, public synthetic A0–A6 checkpointed runner, native sidecar
auditor, builder/wrapper 82-file overlay. CPU02 đạt 2.583 pass/1 skip,
23 focused tests; setup/Ruff/mypy 327 files/knowledge đạt. 456 source/2.859 raw
hashes khớp; 169 data hashes không đổi. Exact preflight03 archive/expanded đạt
7/7 runtime levels, 8 tools/recovery, 21 Dummy/resume; 426 raw files/88 source
files đã kiểm. Source inference cố định `372d685`.
CPU01 và preflight01/02 giữ như development history, không chọn acceptance.
Source/evidence đã push `d1e3e27`. **Đã submit kernel version 1**
`huylmhuhu/react-vn-security-runtime-v1`, timeout 7200s, T4; status **COMPLETE**.
Đã tải và audit `results/phase5_security_runtime_gpu_v1_output01`: 205 raw/two
remote files khớp, local joins bằng byte với remote. 7/7 terminal/recovered;
**0 tool calls/0 guard calls**, 12 workers TERMINATE/-15. Không gọi là 7/7 utility
hoặc native guard/graceful acceptance. Không còn job hay downloader đang chạy.
Không push lại, ghi đè hoặc retry semantic result.
Pull với suffix `/1` bị API 403; pull tên hiện hành vào
`results/phase5_security_runtime_gpu_v1_remote02` thành công, wrapper SHA-256
khớp preflight; metadata private/offline/T4/image/mount đúng. Live logs trả HTTP
500 trong lúc chạy; không nhầm lỗi đọc log thành lỗi inference.

Auditor local `scripts/audit_phase5_security_runtime_gpu.py` và 13 tests mới đạt;
commit `d83d79b`, không sửa inference. Full release QA đã xong:
**2.596 pass/1 skip**, 566,82s, setup/Ruff/mypy 328 files/knowledge đạt.
Output `results/phase5_security_runtime_gpu_release_cpu01`;
receipt `experiments/manifests/phase5_security_runtime_gpu_release_cpu01.json`.
458 source/2.859 raw hashes kiểm lại khớp, 169 data hashes không đổi.
[GPU receipt](../experiments/manifests/phase5_security_runtime_gpu_v1_audit01.json)
SHA-256 `e132a46c23f7ae71abcd8c5c4097fcd8adb6d0aa050c07788841b301ec8e6d5f`.
[Report](../docs/evaluation/phase5_security_runtime_gpu_v1_report.md) ghi timing,
limits và command audit không inference. Scan 207 files/four credential values:
zero matches. Raw generated files không track Git; receipts/report được chọn lưu.
Source pair/runtime v2 và mọi raw lịch sử giữ nguyên.

[Pair/runtime v2](phase5_pair_runtime_v2.md) đã hoàn tất bounded CPU QA:
event-bound host outcomes và explicit failed-startup timing. 64 focused tests;
full **2.560 pass/1 native-tqdm skip** (551,55s), setup/Ruff/mypy 320 files/knowledge đạt.
63 joined receipts, 445 source/641 raw hashes khớp, 169 data hashes không đổi;
971 entries CPU02 v1 kiểm lại vẫn khớp. Mốc CPU v2 này đã kết thúc.
[Receipt v2](../experiments/manifests/phase5_pair_runtime_v2_cpu01.json) SHA-256
`0832ae8c29f925f8bc522ac3138fa6d41132d3dae53ac68d44ffd7bd58a453b9`.
Working-tree CPU QA anchored parent `817da23`; không đổi thành clean release.
CPU02 v1 bên dưới là lịch sử, không sửa source đã hash hoặc output cũ.

Mốc trước: [ModelPair/runtime v7 integration](phase5_pair_runtime_v1.md).
Role adapters đã triển khai; 52 integration tests pass. CPU01 full QA đạt
2.492 pass/1 skip nhưng chưa chọn làm acceptance vì sai nhãn schema trace.
Snapshot source CPU01 là `819af7a`; remediation `be73761` đã push origin/main.
CPU02 hoàn tất tại `results/phase5_pair_runtime_v1_cpu02`: 2.496 pass/1 skip,
477,43s; setup/Ruff/mypy 317 files/knowledge đạt. Lượt CPU02 đã kết thúc.
Schema pair/host ledger audit đạt 51 receipts; 441 source/530 raw hashes khớp,
169 tracked data hashes không đổi. [Receipt](../experiments/manifests/phase5_pair_runtime_v1_cpu02.json)
SHA-256 `1bc819d51f47e90f2fb35ad904087626cbb958ea8665b250a848ec335009312e`.

Owner yêu cầu sửa lỗi audit và hoàn thiện phần thiếu Phase 5, lưu thực nghiệm/tri thức.
Đã thêm runtime v7 và components v2: clause-bound final grants, residual screening,
table/column scope pairs, tích hợp A4–A6 trước Broker, metadata đúng level và
origin extraction cho synthetic student IDs. Không sửa code/receipt v1/v5/v6.

Đã xác nhận 91 focused tests và full QA 2.444 pass/1 native-tqdm skip (460 giây).
Setup/Ruff/mypy 314 files/knowledge đạt cho lượt remediation đã hoàn tất.
Output/receipt:
`results/phase5_remediation_v2_cpu01` và
`experiments/manifests/phase5_remediation_v2_cpu01.json`.
Receipt remediation là working-tree QA tại thời điểm đo; source sau đó đã được
commit `be73761`, không đổi nhãn lịch sử thành clean release.

## Bước tiếp theo

1. CPU native diagnostics v1 đã chốt và kiểm độc lập receipt/source/raw.
   Giữ nguyên các output đã hoàn tất; không chạy trùng hoặc sửa source đã hash.
2. Ghép public Dev input/catalog theo lịch 8 pairs/16 cases đã chốt; không chọn
   lại family theo model outcome. Scope v3 đánh dấu cả 16 trigger là unassessed:
   document/page dùng AWB/AUX; SQL shape hiện tại còn hẹp. Đây là static check,
   không phải 16 model failures hay tỷ lệ chặn đúng. Thêm version riêng cho scope,
   kiểm positive/negative controls, không cấp quyền chỉ vì ID tồn tại trong data.
   Giữ host trust/sensitivity độc lập, unknown sources conservative; không lấy
   private oracle làm catalog. Chi tiết trong [báo cáo](../docs/evaluation/phase5_guard_diagnostics_v1_report.md).
3. Ghép runner/checkpoint/native observer/auditor, freeze run identity và exact
   offline archive/expanded package; kiểm GitHub source trước inference. Chỉ khi
   QA này đạt mới bỏ dispatch-disabled. Kiểm live quyền/quota/private mounts lúc
   submit, ghi notebook/Dataset version thật vào sổ Kaggle. Không cần account mới.
4. Đo đủ guard structured-output/Pre/Post coverage, lỗi và timing cho matched Dev;
   giữ mọi semantic failures, không retry để đổi kết quả. Native lifecycle,
   broader scope và formal freeze còn mở. Không mở Phase 6/7/Test.

Pending access: không cần tài khoản mới. Đã đọc Kaggle skill/preflight và kiểm
quota owner `huylmhuhu` trước run ngày 2026-09-13: GPU còn 29,86h, refresh 2026-09-19.
Đây là snapshot trước run, không quota hiện tại/reservation. Đã kiểm SDK Dataset private/ready/version 1
và kernel name chưa trùng trước upload (2026-09-13).
Không cycling credential.
Tác vụ model nặng chỉ chạy Kaggle, không chạy local.

## Bằng chứng

- [Repair notes](phase5_remediation_v2.md).
- [Receipt mới](../experiments/manifests/phase5_remediation_v2_cpu01.json):
  436 source + 573 raw hashes khớp qua re-audit; 169 tracked data hashes không đổi.
- [Báo cáo QA](../docs/evaluation/phase5_remediation_v2_report.md): 69 runtime
  records, 28 exact parity pairs, 41 v7 Broker calls; không có inference LLM thật.
- [Runtime/component contract](../docs/architecture/phase5_remediation_v2_contract.md).
- [Native pair lịch sử](ordinary_pair_gpu_v1.md): chỉ transport/residency/timing,
  không phải quality/ASR; hai worker trước đó phải TERMINATE/-15.
- Entitlement v1 receipt có hash `pytest.log` sai; không sử dụng `valid=true`
  của nó làm điều kiện nghiệm thu. Giữ nguyên bytes và ghi audit độc lập.
- Runtime v6 raw 101/101 và scope v1 raw 19/19 khớp trong lượt audit; điều đó
  không sửa được lỗi hành vi. Các mốc lịch sử nằm trong từng knowledge note.

## Giới hạn

Phase 5 chưa accepted. CPU tests dùng synthetic/Replay/fake guard, không thay
cho kết quả thực nghiệm bảo mật với LLM. Held-out payload không được mở/tune;
validator chỉ hash tracked data. Không thay dataset hoặc mock network tools.

Giữ nguyên thay đổi ngoài phạm vi của người dùng: `plan/phase6.md`–`phase9.md`,
báo cáo tiến độ và `docs/figures/`. Không stage/xóa các mục này.
