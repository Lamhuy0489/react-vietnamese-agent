# Bàn giao phiên làm việc

Cập nhật: 2026-09-07. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **A3–A5 session policy tích hợp vào ReAct v3**, local synthetic QA pass.
Phase 1–4 accepted; Test vẫn khóa. [Contract](../docs/architecture/phase5_session_contract.md),
[tiến độ](phase5_progress.md). Selected committed-source receipt đang chuẩn bị.

A0/A1 giữ nguyên mechanics; A2 thêm guard Pre-action/Post-source, sticky nguồn
MALICIOUS/error chặn external trước Broker, read-open, SUSPICIOUS chỉ TAG.
Worker thực sự bị terminate/kill/reap khi timeout; không tự restart sau failure.
Guard trace/cache riêng task, ghi identity/hash/cold latency, không vào model context.
A3 max sensitivity/S0 clearance, A4 bounded raw-user external authorization,
A5 sticky joint rule/guard alert/error veto đã tích hợp. Final vẫn pass-through,
A6 chưa operational. Không nghiệm thu toàn Phase 5.

## Bước tiếp theo

1. Đọc phase status, kiểm tra Git/hashes; dùng validator A2 mới trong
   [runbook](runbook.md), không sửa source/test/config đã ghi receipt.
2. Chốt guard model/revision cố định A2–A6; host factory phải tạo model trong
   process, inference local và process-owned. Adapter hiện cold-load mỗi cache
   miss, chưa phải persistent GPU worker hoặc bằng chứng hiệu suất model.
   Cần lifecycle/version hiệu quả hơn được QA riêng trước chạy guard LLM thật.
3. Tiếp theo: A6 value-origin/index/unknown critical deny/Post views/Final protection.
   Đọc phase5 sections và freeze contract trước triển khai; A6 cần adjudication
   riêng thay coarse veto, không nhầm whole-context lineage với nguồn từng token.
   Rà A4 general processing scope ngoài bounded external anchors còn chưa có.
4. Grouped Dev tune/validation protocol trước tuning; không load Test/authoring
   payload hoặc thay seal/frozen source. Không sang Phase 6.
5. Không cần tài khoản mới cho local implementation. Meta access vẫn thiếu cho
   Llama pilot riêng, không chặn A3–A6 local work.

## Bằng chứng

- Session preflight: **593 tests pass**, 147 mới; setup/Ruff/mypy 179 files,
  knowledge pass. 44 A0–A2 exact pairs + 30 session cases = 118 fresh Replay.
  Riêng session cases: 165 fake guard classifications, 225 snapshots, 15 expected
  denials. Không ASR. 127 source/780 raw hashes ghi; 514 prior source entries intact.
  Source-independent state reconstruction đối chiếu labels/rule/guard traces;
  zero-call terminal, repeated denials/fresh state, tamper, dimension matrix,
  current-action/sticky alerts và raw-user negative controls có tests.
- A2 historical source `15ed921`,
  [receipt](../experiments/manifests/phase5_a2_v2_validation01.json) khớp preflight.

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
V3 đã tạo guard sidecar rỗng và session initial/final cho zero-call terminal paths;
v2 giữ nguyên giới hạn lịch sử, không sửa file đã hash.
Rule input vẫn source-native JSON; lexical/anchor false positives/negatives giữ
nguyên, không giả hiểu mọi câu tiếng Việt. A3–A5 coarse veto có thể giảm utility.
A4 hiện external action/destination only, chưa general processing-scope tracking.
Review assistant theo owner waiver, không independent human review.
Không lưu credentials, private GT, Test payload hoặc CoT trong knowledge.
