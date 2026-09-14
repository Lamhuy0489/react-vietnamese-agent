# Bàn giao phiên làm việc

Cập nhật: 2026-09-14. Chỉ dẫn hiện hành; các mốc v1/v6 là lịch sử, không thay thế mục này.

## Đang làm

Đã chốt CPU [native shutdown wiring v2](native_shutdown_wiring_v2.md), source
`dfbd54f`: factory/runner/auditor riêng; 36 focused tests (27,70s), full
**2.740 pass/1 optional-tqdm skip**, 719,76s. Setup/Ruff/mypy 342 files/knowledge
đạt. 478 source/4.726 raw hashes khớp, 169 data hashes không đổi; 15 actual runtime
receipts, 70 native-shaped mocked records tách riêng. [Report](../docs/evaluation/phase5_native_shutdown_wiring_v2_report.md)
và [receipt](../experiments/manifests/phase5_native_shutdown_wiring_v2_cpu01.json),
SHA-256 `fd4c7a3fcc773811545a286d5b23e3b1bfa214526ba115bd54eb3052c1a8e911`.
Output `results/phase5_native_shutdown_wiring_v2_cpu01` đã chốt, không ghi thêm/
chạy trùng; không còn QA chạy. Chưa package v2/GPU mới. Bước tiếp là exact
wrapper/builder và release auditor; calculator chỉ là CPU control, không retry v1.

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

1. Giữ nguyên identity đã hoàn tất; không chạy trùng hoặc ghi thêm vào output.
2. Version wrapper/builder và release auditor theo [checklist exact package](native_shutdown_wiring_v2.md).
   Native composition/runner/auditor v2 đã đạt bounded CPU; không làm lại factory
   hoặc sửa v1 frozen. Kiểm exact archive/expanded mounts, import closure, 8 tools,
   21 public Dummy/resume và CLI mới trước GPU. Giữ riêng partial/unverified native
   evidence; CPU ACK không chứng minh native teardown hoặc GPU recovery.
3. Định trước diagnostic mới cho tool/guard-path coverage (pilot calculator có
   zero tool/guard calls phải giữ nguyên). Sau đó grouped Dev guard quality,
   broader coverage và freeze. Không retry semantic hoặc mở Phase 6/7/Test.

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
