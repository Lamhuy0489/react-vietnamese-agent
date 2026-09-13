# Bàn giao phiên làm việc

Cập nhật: 2026-09-13. Chỉ dẫn hiện hành; các mốc v1/v6 là lịch sử, không thay thế mục này.

## Đang làm

Đang làm [seven-level runtime package](phase5_security_runtime_probe_v1.md):
agent-only factory, public synthetic A0–A6 checkpointed runner, native sidecar
auditor, builder/wrapper 83-file overlay. 22 focused tests pass; cần full QA,
exact archive/expanded mount rồi push/upload. Không có GPU mới tại mốc này.
Source pair/runtime v2 và mọi raw lịch sử giữ nguyên.

[Pair/runtime v2](phase5_pair_runtime_v2.md) đã hoàn tất bounded CPU QA:
event-bound host outcomes và explicit failed-startup timing. 64 focused tests;
full **2.560 pass/1 native-tqdm skip** (551,55s), setup/Ruff/mypy 320 files/knowledge đạt.
63 joined receipts, 445 source/641 raw hashes khớp, 169 data hashes không đổi;
971 entries CPU02 v1 kiểm lại vẫn khớp. Không có job CPU/GPU còn chạy.
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
2. Tiếp [native package/runtime](phase5_pair_runtime_kaggle_next.md): thêm native
   agent-only factory có cùng attention/request policy với paired agent; runner
   v2 và independent native artifact join. Nguồn đã QA phải commit/push trước upload.
   Base bundle03/pins đã kiểm, dependency traversal 90 files/22 bổ sung, chưa
   exact mount preflight. Gói mới cần 8 tools/recovery, 21 public Dummy/resume.
3. Sau exact package, kiểm native GPU lifecycle, guard
   quality trên grouped Dev, kiểm broader coverage và freeze. Chưa mở Phase 6/7.

Pending access: không cần tài khoản mới. Đã đọc Kaggle skill/preflight và kiểm
quota owner `huylmhuhu` ngày 2026-09-13: GPU còn 29,86h, refresh 2026-09-19.
Đây là snapshot, không reservation; kiểm lại owner/private Dataset trước upload.
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
