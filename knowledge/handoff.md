# Bàn giao phiên làm việc

Cập nhật: 2026-09-08. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **A6 value PreGate/Post-view components đã qua synthetic QA**.
[Contract](../docs/architecture/phase5_value_gates_contract.md), [tiến độ](phase5_progress.md).
Selected-source reproduction đang chuẩn bị. Runtime v3 vẫn A0–A5, final pass-through;
không nhận component ALLOW thành full A6 ALLOW hoặc nghiệm thu Phase 5.

PreGate nhận user/proposal host artifacts, schema strict, exact raw-user action/
destination anchors; critical leaves cần typed origins và S0, protected scan cả
JSON keys. Unknown/limits/errors chặn external, fixed reads vẫn allow.
Index roots và raw-source exposure phải khớp hai chiều; không bỏ sót S2 hoặc dùng
public chưa được thấy. Post-view untrusted JSON envelope giữ raw/nhãn/lineage.

## Bước tiếp theo

1. Đọc phase status/contract, kiểm tra Git/hashes; validator value-gates mới trong
   [runbook](runbook.md). Không sửa source/test/contract đã được selected receipt
   hash; thêm version/module riêng cho integration.
2. **Tích hợp A6 runtime**: freeze contract cho composition PreGuard/value/control,
   arbitration coarse A3–A5 veto, actual-context Post-view lineage, proposed/released
   Final logging và trả released content. Không dùng giá trị ALLOW như proof an toàn.
   Final authorization từ host/user policy, không evaluator GT. Thiếu evidence
   unknown critical relations phải fail closed; không hạ nhãn raw artifact.
3. Kế thừa index/final-release source `3b9f565` và receipt phía dưới. Typed matching
   hữu hạn, không suy whole-context lineage thành nguồn từng token. Destination
   anchor grammar và webhook key/leaf profile hạn chế, có thể giảm utility.
4. Chốt guard model/revision A2–A6/lifecycle GPU hiệu quả; adapter hiện cold-load
   mỗi cache miss. Rà A4 general processing scope, grouped Dev tune/validation
   trước tuning. Không đọc Test/authoring payload hoặc sang Phase 6.
5. Không cần tài khoản mới cho local work. Meta access vẫn thiếu cho Llama pilot riêng.

## Bằng chứng

- Preflight02: **769 tests pass**, 73 mới; setup/Ruff/mypy 186 files/knowledge pass.
  24 Pre cases: 4 ALLOW/20 DENY, sáu Post cases. Bốn actual Broker mock calls,
  zero model/guard/Replay runs. 771 prior source entries intact; 132 source/121 raw
  hashes ghi. Không ASR/utility hoặc real-model claims.
- Review phát hiện omitted-observation hole, thêm two-way coverage check/test.
  Preflight01 source-changed bị vô hiệu, giữ logs nhưng không chọn evidence.
  Tests có unknown fields, key/subject leaks, dimensions/authorization, numeric
  leaves, source/exposure integrity, read/schema limits, Post round-trip/label
  preservation và envelope injection delimiters.
- Origin source `3b9f565`,
  [receipt](../experiments/manifests/phase5_value_origin_v1_validation01.json):
  696 tests, 24 synthetic release cases, 130 source/101 raw hashes khớp.
  Evidence commit `06086c1` hoàn tất phần staged trước đó sau hash/knowledge check.
- Session source `8a4ca3d`,
  [receipt](../experiments/manifests/phase5_session_v1_validation01.json):
  593 tests, 118 Replay; 165 fake guard classifications, 225 snapshots.

## Giới hạn

A6 runtime/full Pre/Post/Final còn chưa tích hợp. Value gate chưa kết hợp rule/LLM
control risks; JSON envelope không chứng minh chống mọi prompt injection.
Exact origin chưa hỗ trợ tự do tổng hợp câu/short values/SQL alias semantics;
unknown leaf/key fail closed có thể overblock. Không model-generated provenance.
Final-release default S0 chưa thay policy cho quyền đọc dữ liệu riêng hợp lệ.
Chưa guard LLM thật, Dev tuning hoặc Test payload parsing; Test checks hash-only.
A0–A5 và điểm pilot giữ nguyên; assistant self-review theo owner waiver, không
independent review. Không credentials/private GT/Test payload/CoT trong knowledge.
