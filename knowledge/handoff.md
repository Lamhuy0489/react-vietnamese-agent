# Bàn giao phiên làm việc

Cập nhật: 2026-09-08. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **A6 runtime v4 integration đã tái lập từ source sạch `04ae4c8`**.
[Contract](../docs/architecture/phase5_a6_runtime_contract.md), [tiến độ](phase5_progress.md).
[Selected receipt](../experiments/manifests/phase5_a6_runtime_v1_validation01.json)
khớp preflight01. Chưa Phase 5 acceptance. Không sửa source/test/contract đã khóa.

V4 hỗ trợ cùng loop A0–A6. A6 lưu coarse/value/composed decisions, chỉ gỡ coarse
sensitivity khi có value ALLOW; rule/LLM/error/control veto vẫn giữ. Index từ
raw host user/tool roots, không từ model/derived views. Post view thật vào model
context; final proposed/released có IDs/hashes riêng, runtime trả released text.
Final S0 host policy không cấp quyền đọc hồ sơ riêng; không lấy grants từ GT.

## Bước tiếp theo

1. Đọc [runbook](runbook.md), kiểm tra Git/hashes. Giữ nguyên source v4 và các
   components đã hash; mở module/version mới nếu cần sửa hành vi.
2. **Guard lifecycle tiếp theo**: predeclare worker dùng lại model qua nhiều
   request, giữ timeout/identity/cache isolation, cancellation/kill/reap và
   retirement khi lỗi. Thêm fake-worker tests trước model/Kaggle thật; không
   âm thầm đổi timeout semantics hoặc bỏ chi phí cold start khỏi số đo.
3. Chốt guard model/revision và worker GPU; rà A4 processing scope và grouped
   Dev tune/validation trước tuning. Không sang Phase 6 hoặc đọc Test payload.
4. General private-record final entitlement và broader value coverage vẫn thiếu;
   không diễn giải S0 profile như đã giải quyết quyền truy cập riêng tư hợp lệ.
5. Không cần tài khoản mới cho local work. Meta access thiếu cho Llama pilot riêng.

## Bằng chứng

- Preflight01: **845 tests pass**, 76 mới, trong 178,13 giây. Setup/Ruff/mypy
  190 files/knowledge pass; 135 source/435 raw hashes kiểm lại.
- 903 prior source entries nguyên vẹn; clean/adversarial seals hash-only pass.
- 26 synthetic runtime conditions + 12 prior-level parity pairs = 50 Replay,
  56 mock Broker calls và 121 fake guard classifications; report valid=true.
- Selected source `04ae4c8`: stable summary khớp preflight, **845 tests pass** trong
  178,29 giây; 135 source/435 raw hashes kiểm lại. 25 A6 final effects: 23 ALLOW,
  1 REDACT, 1 DENY; một A5 pass-through. Không benchmark success/ASR claims.
- Audit bổ sung preflight 50 traces: Broker execution chỉ sau PRE ALLOW, không
  duplicate execution; legacy final answer khớp released RunResult text.
- Source `a3743a2`, [value-gate receipt](../experiments/manifests/phase5_value_gates_v1_validation02.json):
  769 tests, 132 source/121 raw hashes khớp; evidence/GitHub commit `3c3f7fe`.
- Origin source `3b9f565`,
  [receipt](../experiments/manifests/phase5_value_origin_v1_validation01.json):
  696 tests, 24 release cases. Session source `8a4ca3d`,
  [receipt](../experiments/manifests/phase5_session_v1_validation01.json): 593 tests.

## Giới hạn

Không real guard/LLM/Kaggle run, không benchmark Dev tuning hoặc Test parsing.
Exact origin không chứng minh model-internal causal provenance; short values,
SQL aliases, paraphrase, encoding và email case changes chưa được bao phủ đầy đủ.
Unknown critical leaves fail closed có thể overblock. Post envelope không chứng
minh chống mọi injection. Terminal completed chỉ kết thúc loop, không security
success; phải đọc final effect/released field. Assistant self-review theo owner
waiver, không independent review. Không credentials/private GT/Test payload/CoT
trong knowledge; không đưa knowledge vào model prompts.
