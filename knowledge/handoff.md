# Bàn giao phiên làm việc

Cập nhật: 2026-09-07. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

**Phase 5 đã được owner cho phép**, shared ReAct runtime A0/A1 đã pass.
Phase 1–4 accepted; Test vẫn khóa. Source `d2ec2d5`,
[receipt](../experiments/manifests/phase5_runtime_v1_validation01.json),
[contract](../docs/architecture/phase5_runtime_contract.md),
[tiến độ](phase5_progress.md).

Đã có config A0–A6 strict/cumulative, quyết định bảo mật có reason codes,
A1 raw/normalized rules và raw-user anchors, vòng ReAct A0/A1 qua Tool Broker.
Raw model/context/action/argument/final có lineage; denied action không chạy tool,
không giả ToolResult; feedback artifact riêng để model tiếp tục theo step budget.
A2 chỉ có interface/prompt/parser/cache/error handling, chưa guard inference thật.
Không nhận bảy config là bảy mức đã operational, không nghiệm thu Phase 5.

## Bước tiếp theo

1. Kiểm tra [phase status](../docs/project/phase_status.md), Git và source hashes.
   Chạy quality/component validator theo [runbook](runbook.md).
2. Shared runtime A0/A1 đã có. Giữ source đã hash, dùng module/version kế tiếp
   khi tích hợp mức mới; không đổi rule/config/receipt đã chọn. Xác nhận không
   bypass Broker/Pre/Post/Final và luôn có differential A0 parity.
3. **Chốt model/revision của guard dùng chung A2–A6**; bổ sung timeout/cancellation
   có hiệu lực trước actual inference. Adapter hiện xử lý TimeoutError do backend
   trả, không giả có khả năng ngắt GPU job. Không cần tài khoản mới cho phần local.
4. A3 sensitivity, A4 trust/control và A5 combined session; sau đó A6 value-origin
   + sensitive-value index/unknown critical deny/Post views/Final protection.
   Đọc các mục tương ứng trong [phase5](../plan/phase5.md) trước triển khai.
5. Chia grouped Dev tune/validation trước tuning. Không load authoring/Test payload,
   không thay seal/frozen source và không điều chỉnh dựa trên Test. Không sang Phase 6.
6. Meta access vẫn thiếu cho Llama pilot riêng, không chặn component work.

## Bằng chứng

- Runtime selected: **366 tests pass**, 66 tests mới; setup/Ruff/mypy 170 files.
  20 smoke exact A0 pairs + 24 synthetic A0/A1 conditions = 64 fresh Replay.
  655 artifacts của các run Phase 5, sáu micro-case denials đúng kỳ vọng; không ASR.
  120 source/369 raw hashes khớp, 270 prior source entries giữ nguyên. Stable
  summary khớp preflight; selected run từ clean source commit. No model/benchmark
  Dev/Test payload parsing. Lỗi detector, repeated denials, parse retry, model error,
  audit-view isolation, final pass-through và fresh state đều có regression tests.
- Component dưới đây là mốc lịch sử, vẫn giữ nguyên source/evidence.

- **300 tests pass**, gồm 56 synthetic Phase 5 micro-tests. Setup/Ruff/mypy
  **166 files** pass. Selected component receipt ghi source sạch trước chạy.
- A0 bypass detector; A1 read-only allow, source TAG/raw preservation, external
  deny trước Broker và explicit-authorized control. Session signal reset.
- Strict config/GT rejection; guard JSON duplicate/unknown/extra reasoning rejection,
  identity/cache tests và read-open/sink-closed khi timeout/backend error.
  Đây là Replay/fake backend tests, không ASR/LLM-quality evidence.
- 153 frozen Phase 4 source hashes đã check; component validator hash-only Test,
  không benchmark Dev run, không guard/model inference mới.
- Phase 4 source `be7f8b5`,
  [closure](../experiments/manifests/phase4_closure_v1_validation01.json):
  244 tests, 45 Dev pairs/90 Replay + 440 overhead + hai stress. Raw/data/source
  và điểm pilot trước giữ nguyên. Gemma 6/21, Qwen7B 3/21 Dev.

## Giới hạn

Phase 5 đang làm, runtime chỉ hỗ trợ A0/A1, chưa full A2–A6 architecture. A1 lexical rules có
false positives với trích dẫn; raw-user anchor grammar có false negatives và không
chứng minh hiểu mọi ý định. Rule input là source-native JSON snapshots, không
đảm bảo detection qua mọi JSON escape/phrase split. Final A0/A1 chưa bảo vệ rò rỉ.
A6 phải tách exposure/value-origin, không biến whole-context taint thành proof
nguồn từng token. Chưa sửa frozen artifacts để declassify.
Review assistant theo owner waiver, không independent human review.
Không lưu credentials, private GT, Test payload hoặc CoT trong knowledge.
