# Bàn giao phiên làm việc

Cập nhật: 2026-09-08. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **guard-only GPU v1 COMPLETE và audit; chưa quality/graceful acceptance**.
[Báo cáo](../docs/evaluation/phase5_guard_gpu_v1_report.md),
[receipt](../experiments/manifests/phase5_guard_gpu_v1_audit01.json),
[audit deviation](../docs/evaluation/phase5_guard_gpu_audit_deviation.md).
First submission kernel `huylmhuhu/react-vn-guard15-probe-run-v1` version1,
id133519671, private/offline/T4. Runtime source `7649d5b`, bootstrap `9680c81`,
source/receipt push `0e1bc2d` trước GPU. Không submit lần hai.

Bốn output đúng schema, ba A khớp hash nhưng **B cũng SAFE**, cả bốn giống nhau.
Cold requests47,895/32,814s; warm0,956/0,991s; peakallocated2,898GiB.
Hai workers PID34/62 TERMINATE/-15/reaped, không graceful. Auditor v1 reject
`worker cleanup`; v2 giữ failure, báo integrity/repeatability/graceful riêng.
Không sửa frozen inference source hoặc raw; không chốt Qwen1.5B làm guard.

## Bước tiếp theo

1. Full QA đã hoàn tất: **1.046 tests/276,16 giây**, basetemp
   `build/pytest_guard_gpu_audit_v2_01`; không test/kernel/upload đang chạy.
   Targeted23tests pass (17 v2 audit + six Dummy release audit), lint/mypy208files
   gồm wrapper/setup/knowledge pass. Audit/report tái tạo hai lần khớp bytes.
   [Release QA receipt](../experiments/manifests/phase5_guard_gpu_v1_release_qa01.json).
2. Predeclare technical cancellation/GPU-memory-recovery probe. Hiện biết hai
   workers cần terminate; chưa đo VRAM trực tiếp sau reap, chưa biết nguyên nhân
   cleanup chậm. Không tăng grace hoặc rerun classification rồi bỏ kết quả cũ.
   Nếu thay lifecycle/config, dùng version mới và giữ source/receipt hiện tại.
3. Versioned agent placement và concurrent-residency/context stress. Old
   MeasuredHFBackend13GiB/device không tái dùng nguyên cho agent+guard.
   Guard-only peak không combined fit hoặc general context bound proof.
4. Grouped Dev protocol/model decision rồi A4 scope/general final entitlements.
   Không tune từ four-call result hoặc held-out Test. Phase 5 chưa accepted.
   Không Phase 6/7, không benchmark Test, không cần tài khoản mới.
5. Account `huylmhuhu` (kaggle1), CLI `python3 -m kaggle`2.2.4.
   Pre-submit quota29,49h còn; không coi đó là quota hiện tại được giữ chỗ.
   Không đổi account để vượt quota. Không token/key trong logs/memory.

## Bằng chứng

- 1.046 full tests pass; 23 tests mới cho v2 audit/Dummy release audit.
  Source/module/test/report hashes được khóa trong release QA receipt.

- Raw `results/phase5_guard_gpu_v1_raw01`: **56 files**, full log + Dummy/guard.
  Remote source `build/kaggle/guard_gpu_v1_remote_source02`; versioned pull /1
  403, latest pull thành công; wrapper hash khớp receipt. Metadata chứa image digest.
- Selected audit/report ở `results/phase5_guard_gpu_v1_release_audit03`;
  audit04 tái tạo khớp bytes. Audit01/02 giữ lịch sử trước khi làm rõ câu mô tả
  hai T4 allocated nhưng hai guard workers tuần tự chỉ ở device1; số đo không đổi.
  Checked-in receipt/report là bản copy đúng bytes từ audit03.
  21Dummy unique runs/84schema-valid events/checkpoint hashes/input identity pass.
  Credential scan60files gồm raw/audit/source:0matches. Test hash-only prerequisites.
- V2 bootstrap `build/kaggle/phase5_guard_mount_v2_preflight01/kernel`,
  [preflight](../experiments/manifests/phase5_guard_mount_v2_preflight01.json):
  archive và actual expanded PAX pass isolated offline, eight tools/fault,
  21Dummy/completed+missingonly resume, four-callstub mỗilayout. 1.023tests pass.
- Original Dataset `huylmhuhu/react-vn-guard15-probe-data-v1` READY/v1/private,
  id11942593; bundle03 `build/kaggle/phase5_guard_probe_v1_bundle03` giữ nguyên.
  [PAX rejection](../experiments/manifests/phase5_guard_remote_mount_v1_diagnostic01.json)
  xảy ra trước GPU. Metadata sidecar xử lý exact commit, không ignore mọi extras.
- Weights `build/guard_models/qwen1_5b_hf_v1_acquisition01`: ten files,
  3.098.973.447bytes, publisher hashes pinned, revision
  `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
- Frozen adapter source `bc2023f`, warm `2300751`, v4 `04ae4c8` giữ nguyên.
  134 adapter source hashes đã kiểm lại trước GPU; không sửa selected files.

## Giới hạn

Model quality không đạt diagnostic B; repeatability không discrimination proof.
V1 graceful audit vẫn fail; v2 integrity flag không chuyển failure thành pass.
Raw response chỉ giữ hash và valid JSON, không thể tái hash raw từ parsed JSON.
Free-memory endpoints không global peak; process reap không đo VRAM recovery.
No agent resident, no combined/context/cancellation stress. No semantic retry,
benchmark inference/Test payload/GT/CoT hoặc project memory trong model prompts.
Assistant self-review theo owner waiver, không independent human review.
