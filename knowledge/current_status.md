# Trạng thái hiện tại

Cập nhật: 2026-09-14. **Phase 5 đang làm, chưa nghiệm thu.**

## Hiện hành — sửa lỗi sau audit

Ưu tiên mới: [host-bound resource scope v4/runtime v9](resource_scope_v4.md).
Đã ghép catalog public Dev và quyền đọc AWB/AUX theo host metadata + raw user.
Full **2.945pass/1skip/865,40s**, 75focused/25,18s, setup/Ruff/mypy371/knowledge
đạt; 524source/295raw/169data hashes khớp. Source `d9f11df`,
[CPU receipt](../experiments/manifests/phase5_resource_scope_v4_cpu01.json).
Không còn QA chạy; SQL row scope và exact Dev package còn thiếu. Không có GPU
job mới, không đổi benchmark hoặc mở Test, chưa tăng gate nghiệm thu.

Đang làm [guard diagnostics v1](guard_diagnostics_v1.md): sanitized observer và
CPU retirement/parity controls đạt full2.871pass/1skip (714,93s), 510source/424raw
hashes khớp, 169data unchanged. Kế hoạch Dev cố định8pairs/16cases đã lưu, chưa
dispatch GPU. Native observer/auditor đạt full **2.888pass/1skip**, 785,14s;
75focused/64,83s, setup/Ruff/mypy365/knowledge đạt, source `c7fa18c`.
515source/567raw/169data hashes kiểm lại khớp; 51 runtime receipts được audit.
[Native CPU receipt](../experiments/manifests/phase5_native_diagnostics_v1_cpu01.json)
đã chốt; không còn QA chạy. Bước kế Dev input/catalog, bounded scope và package.
[Báo cáo hiện hành](../docs/evaluation/phase5_guard_diagnostics_v1_report.md).

Đã chốt [document diagnostic v1](document_diagnostic_v1.md), source
`54aa3ec`: scope v3/runtime v8 sửa bounded CDOC. Full **2.813 pass/1 skip**,
693,77s; 49 focused tests; setup/Ruff/mypy 357 files/knowledge đạt. 501 source/
158 raw hashes CPU và 110 source/430 raw hashes exact preflight đều khớp,
169 data hashes không đổi. GitHub `8836e9c` đã push; **đã submit notebook
`huylmhuhu/react-vn-document-runtime-v1` version1**, T4/7200s/private/offline.
[Submission receipt](../experiments/manifests/phase5_document_gpu_v1_submission01.json).
**Version1 COMPLETE/artifact audit đạt**: 261raw/2remote khớp; 7doc reads,
A0/A1 completed, A2–A6 model_error: guard PRE INVALID_OUTPUT, retire đóng pair,
POST BACKEND_FAILURE. 8GRACEFUL/4TERMINATE, 12reaped, 7recovered. Không còn job/
downloader; [GPU receipt](../experiments/manifests/phase5_document_gpu_v1_audit01.json).
Bước kế CPU error-diagnostic/fallback audit rồi prereg grouped Dev guard quality;
không retry semantic. Không làm lại các mốc cũ bên dưới.

Đã chốt [shutdown package v2](shutdown_package_v2.md), source `fa28401`:
exact archive/expanded preflight01 đạt (101 source/430 raw hashes khớp), 24 focused
tests; full **2.764 pass/1 skip**, 693,35s, setup/Ruff/mypy 346 files/knowledge đạt.
485 source/137 raw hashes CPU QA khớp, 169 data hashes không đổi.
Không còn QA chạy; không submit GPU mới. Tên kernel v2 chỉ là tên dự kiến.
Bước tiếp là diagnostic native mới có mục tiêu lifecycle/tool/guard-path định
trước và identity/package riêng, không retry calculator v1; rồi grouped Dev/freeze.

Đã chốt CPU [native shutdown wiring v2](native_shutdown_wiring_v2.md), source
`dfbd54f`: factory/runner/auditor mới, 36 focused tests; full **2.740 pass/1 skip**,
719,76s. Setup/Ruff/mypy 342 files/knowledge đạt; 478 source/4.726 raw hashes khớp,
169 data hashes không đổi. 15 actual runtime receipts và 70 mocked native-shaped
records tách riêng. Mốc wiring đã xong; package v2 phía trên nối tiếp mốc này.
Chưa GPU mới; không dùng calculator v1 để semantic retry.

Đã chốt CPU [pair/runtime v3](pair_runtime_v3.md), source `c4afb83`: 74 focused
tests, 63 runtime receipts join hợp lệ; full **2.704 pass/1 optional-tqdm skip**,
670,56s. Setup/Ruff/mypy 335 files/knowledge đạt; 468 source/646 raw hashes khớp,
169 data hashes không đổi. [Receipt](../experiments/manifests/phase5_pair_runtime_v3_cpu01.json)
đã selected; mốc này đã xong. Wiring CPU v2 phía trên nối tiếp mốc này;
exact package/GPU/quality/freeze vẫn chưa đóng.

Mốc đã chốt trước là [worker shutdown v2](worker_shutdown_v2.md): standalone CPU, chưa nối
ModelPair/GPU. 80 focused tests đạt (34 mới + 46 regression cũ); full QA
**2.630 pass/1 optional-tqdm skip**, 581,50s. 462 source/677 raw hashes khớp,
169 data hashes không đổi. Job standalone đã xong. Bước tiếp sau CPU v3 là
[native wiring và lifecycle audit](worker_shutdown_integration_next.md).
Tra tài nguyên chung tại [sổ notebook/Dataset Kaggle](kaggle_resources.md).

Mốc native gần nhất: [seven-level native package](phase5_security_runtime_probe_v1.md)
đạt CPU02: **2.583 pass/1 skip**, 23 focused tests; setup/Ruff/mypy/knowledge đạt.
456 source/2.859 raw hashes khớp, 169 data hashes không đổi. Exact preflight03
archive/expanded đều đạt 7/7 synthetic runtime levels và base tool/Dummy/resume.
Source `372d685` đã push trước native run. Kernel version 1 **COMPLETE và audit đạt**:
205 raw/2 remote files khớp; 7/7 terminal completed, VRAM recovered. Nhưng 0 tool
calls/0 guard calls, 12 worker TERMINATE/-15. Chưa đóng native lifecycle/quality.
Release auditor QA 2.596 pass/1 skip; 13 tests mới, setup/Ruff/mypy/knowledge đạt.
Không còn job GPU chạy; [báo cáo](../docs/evaluation/phase5_security_runtime_gpu_v1_report.md)
và [handoff](handoff.md) ghi kết quả/bước tiếp, không submit trùng.

Mốc trước: [pair/runtime v2 failure evidence](phase5_pair_runtime_v2.md).
Đã kiểm process chết sau worker response cho cả hai role/victim, nối host outcome
với pair event ledger; failed startup có elapsed thực tế và cờ completion.
64 focused tests, full QA **2.560 pass/1 skip** (551,55s), 63 joined receipts;
445 source/641 raw hashes khớp, 169 data hashes không đổi và CPU02 v1 nguyên vẹn.
Chưa có runtime GPU mới. Bước tiếp: native agent-only factory tương đương paired
agent, runner và exact archive/expanded package preflight.

Mốc trước là [ModelPair/runtime v7 bounded CPU integration](phase5_pair_runtime_v1.md):
A0/A1 chỉ agent, A2–A6 hai worker sibling qua parent role adapters. Đã tách schema
pair và host proposals khỏi transport attempts. CPU02 có 52 focused tests,
full QA **2.496 pass/1 skip** (477,43s), 51 joined receipts, 441 source/530 raw
hashes khớp và 169 tracked data hashes không đổi. CPU01 giữ làm lịch sử, không
selected acceptance vì schema trace cũ sai. Không có GPU run mới; xem [handoff](handoff.md).

Bản phát triển mới là `security_runtime_v7`, đi với final entitlement v2,
processing scope v2 và typed value origin v2. Không dùng v1 entitlement/runtime v6
cho thí nghiệm mới: audit phát hiện cấp quyền chéo, supplied-grant validation yếu,
bỏ sót bản zero-width đi kèm raw và metadata A0 tự nhận policy A6.

V7 ghép bounded A4 scope trước Broker ở A4–A6; giữ scope theo task, ghi trace
và không đổi prompt/tools/decoding. Kiểm thực tế database smoke còn phát hiện
synthetic ID bị bộ origin v1 bỏ qua; v2 bổ sung profile có giới hạn.

91 focused tests pass; full QA **2.444 pass/1 native-tqdm skip** trong 460 giây.
Setup/Ruff/mypy 314 files/knowledge đạt. Receipt được audit độc lập:
436 source/573 raw hashes khớp, 169 tracked data hashes không đổi.
[Receipt](../experiments/manifests/phase5_remediation_v2_cpu01.json) là working-tree
CPU QA, không gọi là clean release; xem [handoff](handoff.md).
[Chi tiết sửa lỗi và bằng chứng](phase5_remediation_v2.md).

## Bằng chứng cần phân biệt

- Entitlement v1 selected receipt có hash `pytest.log` sai: giữ nguyên để audit,
  rút lại việc coi receipt này là bằng chứng toàn vẹn.
- Runtime v6 raw hashes khớp nhưng test cũ không bao phủ các lỗi hành vi đã tìm ra.
- Native Qwen 7B/1.5B trên T4×2 đã chạy 6 calls kỹ thuật; đó không phải benchmark
  chất lượng guard/ASR/utility. Worker cleanup cũ là forced, không graceful.
- Phase 1, clean_v1.1 Phase 2, adversarial_v2 Phase 3 và Phase 4 đã được nghiệm thu
  theo phạm vi/owner waiver ghi trong phase status. Không mở lại Test để tuning.

## Các gate còn mở

1. Native ModelPair/runtime packaging và GPU lifecycle; CPU integration đã đạt
   phạm vi kiểm thử đã ghi, chưa chứng nhận mọi native failure/timing condition.
2. Production guard quality và grouped Dev differential validation.
3. Broader semantic origin/scope coverage và formal Phase 5 freeze.

Không lấy số test pass làm phần trăm hoàn thành. Không chuyển Phase 6/7.
[Tiến độ/gate](phase5_progress.md) · [Chỉ mục tri thức](README.md).
