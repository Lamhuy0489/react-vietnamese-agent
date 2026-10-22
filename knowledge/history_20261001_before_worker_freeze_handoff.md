# Bàn giao phiên làm việc

> Ưu tiên 2026-10-01: đã tạo hai owner review exports tại
> `build/kaggle/collaborator_pair_review_20261001_01/owner_handoff` cho
> lamhuy8904/agent và meanalways/guard. Preflight4/4, notebook code-byte equality
> và compile2/2 đạt. Không credential/account login/remote action; chưa API key.
> Đây là review-only `development`; **source freeze/push còn phải làm trước upload**,
> sau đó mỗi chủ tài khoản tự chạy trên tài nguyên được phép. Không cho bên khác
> dùng credential để luân phiên quota. [Receipt](../experiments/manifests/phase5_collaborator_review_20261001.json).
> Native v2 runner đã triển khai/CPU-tested ở lượt30/09, không cần viết lại.
> Pending access: chưa có owner-started workers hoặc nguồn compute hợp lệ khác;
> không cần gửi lại key Kaggle. Khi worker thật READY mới authenticated discovery.


> Ưu tiên 2026-09-30: runner native v2 và worker entrypoint đã bổ sung;
> 80 targeted tests +4/4 package QA đạt, chưa native/deploy/source freeze.
> Hai tài khoản trước có quota0 ở lần kiểm gần nhất; không luân phiên tài khoản
> để vượt quota. [Báo cáo mới](../docs/evaluation/phase5_native_closure_v2_preparation_20260930.md).
> Bước kế: source freeze và end-to-end discovery/native khi có compute được phép.
> Lệnh status bị ngắt chưa có receipt; không suy trạng thái notebook hiện tại.

Cập nhật: 2026-09-29. Phase5 chưa accepted; Test/private GT giữ khóa.

## Đang làm

Sửa integrity của closure candidate và gói worker API; chỉ Phase5. Owner đã
cho tiếp tục và sửa từ gốc, không cần hỏi lại key hay quyền làm CPU.
[Báo cáo đang áp dụng](../docs/evaluation/phase5_root_fix_20260929.md).
Candidate entrypoint `phase5_closure_runtime_v1.py` bọc v14 integration, giữ
nguyên implementation/candidate metadata. Cùng marker không chứng minh parity.

## Bước tiếp theo

1. Viết runner native version mới: manifest/source/evaluator/task/environment/
   model/worker boot pins phải freeze trước request, không sửa manifest để resume.
   Native entrypoint `run_phase5_native_closure_v1.py` đã nghỉ; các fixture sửa
   vẫn được runner CPU dùng. Không retry hai epoch v1 uncertain cũ.
2. Kết nối end-to-end launcher/discovery/lifetime v3 và factory. Package builder
   hiện chỉ có prepare/preflight; chưa có deployment action. Factory đã đọc đúng
   envelope v3 và từ chối worker đổi boot. Kiểm shutdown/tunnel failure trước GPU.
3. Sau QA gói cuối, source freeze + push theo experiment-repro; submit hai notebook
   private một lần, ghi actual handles/versions trong kaggle_resources. Owner đã
   cho sửa/triển khai, không cần xin lại key. Chưa có blocker cần owner thao tác.
4. Chạy matched Dev đã predeclare và guard fault/paired classifier controls; map
   bằng chứng từng DoD theo plan. Forced Replay và model tự tránh attack là hai
   loại evidence khác nhau; không yêu cầu model leak để chứng minh safety.

## Bằng chứng

- CPU raw: `build/evaluation/phase5_native_closure_cpu_admission04`; 84 completed,
  control_failures=[], source snapshot và terminal checkpoint SHA. Independent
  score `build/evaluation/phase5_native_closure_cpu_admission04_controls.json`:
  44/44 protection rows, full matrix true, phase5_accepted=false.
- Readiness02 trên CPU04: 84 rows, 85 native-identity failures đúng kỳ vọng
  (manifest + 84 Replay executions), phase5_accepted=false. Không auto-promote DoD.
- Package `build/kaggle/request_worker_v3_candidate_20260929_04/preflight_v3/receipt.json`:
  4/4 agent/guard × code_file_only/expanded; 9 source modules; socket interdiction.
- A0 parity test chạy 20 synthetic smoke tasks; candidate markers giữ nguyên;
  checkpoint tamper/path/symlink/order/false acceptance có regression controls.
- Native release04a agent v8/guard v6 và raw epoch01/recovery01 bất biến:
  [recovery report](../docs/evaluation/phase5_native_closure_recovery_report_20260929.md).

## Giới hạn

Chưa có native v3, chưa health live lại, chưa GPU/lifetime proof; chưa đủ 20 DoD.
Không claim guard confusion matrix từ risk counts. C11/C12 actual fixtures không
phải timeout/paired classifier dataset như đề xuất cũ. Historical CPU01 lỗi đầu
đã bị lượt trước ghi đè; report ghi rõ mất raw, không suy là toàn bộ evidence còn.
Package01/02 failures vẫn giữ. Không sửa frozen pin chỉ để pytest xanh.

Pending access: không thiếu API key; credentials vẫn trong nơi lưu private,
không in chúng. Trước native phải xác minh availability/identity mới. QA chi tiết
được cập nhật tại report/receipt sau khi hoàn tất.

[Lịch sử bàn giao trước lượt sửa](history_20260929_before_root_fix_handoff.md).

## QA đã chốt

[Receipt](../experiments/manifests/phase5_root_fix_cpu_20260929.json): 148 tests
liên quan đạt sau HTTP rerun ngoài sandbox; 7 package regression tests mới đạt;
setup/Ruff/mypy626/knowledge-check/diff-check đạt. Full pytest dừng sau
854 passed, 1 skipped (thiếu jsonschema), chưa hoàn tất. Không còn pytest nền.
Readiness02/03 byte-identical. Package04 4/4 đạt, pin launcher/probe hashes;
package03 và các lỗi trước giữ nguyên. Chưa freeze/commit source đang dở.
