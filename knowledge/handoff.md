# Bàn giao phiên làm việc

Cập nhật: 2026-09-08. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **A6 runtime v4 integration đã qua preflight**.
[Contract](../docs/architecture/phase5_a6_runtime_contract.md), [tiến độ](phase5_progress.md).
Preflight `results/phase5_a6_runtime_v1_preflight01` valid; selected reproduction
đang chuẩn bị. Chưa Phase 5 acceptance. Không sửa source/test/contract đã xác minh.

V4 hỗ trợ cùng loop A0–A6. A6 lưu coarse/value/composed decisions, chỉ gỡ coarse
sensitivity khi có value ALLOW; rule/LLM/error/control veto vẫn giữ. Index từ
raw host user/tool roots, không từ model/derived views. Post view thật vào model
context; final proposed/released có IDs/hashes riêng, runtime trả released text.
Final S0 host policy không cấp quyền đọc hồ sơ riêng; không lấy grants từ GT.

## Bước tiếp theo

1. Preflight đã đạt setup/Ruff/mypy/pytest/knowledge, stable cases và hashes.
   Commit source, selected reproduction từ source sạch
   với `--reference` preflight, output/report mới. Xem [runbook](runbook.md).
2. Kiểm lại selected source/raw hashes; cập nhật status/evidence/knowledge, commit
   nhỏ rồi đồng bộ GitHub. Không sửa source đã được receipt khóa.
3. Sau mốc runtime: guard model/revision và lifecycle GPU hiệu quả; adapter hiện
   cold-load mỗi cache miss. Rà A4 processing scope và grouped Dev tune/validation
   trước tuning. Không sang Phase 6 hoặc đọc Test payload.
4. General private-record final entitlement và broader value coverage vẫn thiếu;
   không diễn giải S0 profile như đã giải quyết quyền truy cập riêng tư hợp lệ.
5. Không cần tài khoản mới cho local work. Meta access thiếu cho Llama pilot riêng.

## Bằng chứng

- Preflight01: **845 tests pass**, 76 mới, trong 178,13 giây. Setup/Ruff/mypy
  190 files/knowledge pass; 135 source/435 raw hashes kiểm lại.
- 903 prior source entries nguyên vẹn; clean/adversarial seals hash-only pass.
- 26 synthetic runtime conditions + 12 prior-level parity pairs = 50 Replay,
  56 mock Broker calls và 121 fake guard classifications; report valid=true.
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
