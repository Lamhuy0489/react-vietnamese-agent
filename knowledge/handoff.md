# Bàn giao phiên làm việc

Cập nhật: 2026-09-07. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **A2 process guard đã tích hợp vào ReAct v2**, local synthetic QA pass.
Phase 1–4 accepted; Test vẫn khóa. [Contract](../docs/architecture/phase5_a2_runtime_contract.md),
[tiến độ](phase5_progress.md). Source `15ed921`,
[selected receipt](../experiments/manifests/phase5_a2_v2_validation01.json) từ source
sạch, stable summary khớp preflight; 124 source/548 raw hashes đã kiểm lại.

A0/A1 giữ nguyên mechanics; A2 thêm guard Pre-action/Post-source, sticky nguồn
MALICIOUS/error chặn external trước Broker, read-open, SUSPICIOUS chỉ TAG.
Worker thực sự bị terminate/kill/reap khi timeout; không tự restart sau failure.
Guard trace/cache riêng task, ghi identity/hash/cold latency, không vào model context.
A3–A6 chưa operational, final vẫn pass-through. Không nghiệm thu toàn Phase 5.

## Bước tiếp theo

1. Đọc phase status, kiểm tra Git/hashes; dùng validator A2 mới trong
   [runbook](runbook.md), không sửa source/test/config đã ghi receipt.
2. Chốt guard model/revision cố định A2–A6; host factory phải tạo model trong
   process, inference local và process-owned. Adapter hiện cold-load mỗi cache
   miss, chưa phải persistent GPU worker hoặc bằng chứng hiệu suất model.
   Cần lifecycle/version hiệu quả hơn được QA riêng trước chạy guard LLM thật.
3. A3 sensitivity, A4 trust/control, A5 combined session; A6 value-origin/index/
   unknown critical deny/Post views/Final protection. Không nhầm coarse sticky
   A2 veto với proof nguồn giá trị. Đọc phase5 sections trước mỗi phần triển khai.
4. Grouped Dev tune/validation protocol trước tuning; không load Test/authoring
   payload hoặc thay seal/frozen source. Không sang Phase 6.
5. Không cần tài khoản mới cho local implementation. Meta access vẫn thiếu cho
   Llama pilot riêng, không chặn A3–A6 local work.

## Bằng chứng

- Preflight: **446 tests pass**, 80 mới; setup/Ruff/mypy 175 files/knowledge pass.
  40 exact A0/A1 smoke pairs + chín synthetic A2 = 89 fresh Replay, 31 fake guard
  classifications. 124 source/548 raw hashes ghi, 390 prior source entries intact.
  Timeout và SIGTERM-ignore được kill/reap; crash/invalid output/identity/cache
  retirement, sticky source errors, fresh policy, denied Broker separation và
  guard trace tampering có tests. Không ASR, utility hay GPU throughput claim.
  Selected reproduction cũng pass toàn bộ 446 tests và cùng stable summary.
- V1 source `d2ec2d5`,
  [receipt](../experiments/manifests/phase5_runtime_v1_validation01.json):
  366 tests, 20 A0 pairs + 24 A0/A1 micro conditions, 64 Replay.
- Component source `4bddd23`,
  [receipt](../experiments/manifests/phase5_components_v1_validation01.json): 300 tests.
- Phase 4 source `be7f8b5`,
  [closure](../experiments/manifests/phase4_closure_v1_validation01.json): 244 tests.
  Điểm pilot cũ Gemma 6/21, Qwen7B 3/21 Dev giữ nguyên.

## Giới hạn

Chưa chọn/chạy guard LLM thật, chưa benchmark Dev tuning hoặc Test payload parsing.
Local factory không được mở remote inference/detached job/descendant workers;
adapter không chứng minh ngắt được GPU job bên ngoài process đó.
Guard sidecar hiện được tạo khi có classification; A2 final-only/parse/model-error
trước action không có file guard trace. Mở rộng QA zero-call trước batch guard thật.
Rule input vẫn source-native JSON; lexical/anchor false positives/negatives giữ
nguyên, không giả hiểu mọi câu tiếng Việt. A2 sticky veto có thể giảm utility.
Review assistant theo owner waiver, không independent human review.
Không lưu credentials, private GT, Test payload hoặc CoT trong knowledge.
