# Phase 4 — primitive foundation

Owner authorized 2026-09-07. [Contract](../docs/architecture/phase4_foundation_contract.md)
và [kế hoạch](../plan/phase4.md). Đây là mốc đầu, không phải nghiệm thu Phase 4.

Source `a4e9a87`; [receipt Dev QA](../experiments/manifests/phase4_primitives_v1_validation01.json).
Selected run khớp stable summary của preflight; source hashes đã đối chiếu.
Thời gian normalizer có ghi trong receipt như diagnostic local, không LLM latency.

Đã có:

- `raw_v1`, `unicode_v1`, `security_v1`; raw giữ nguyên, views tách riêng,
  Unicode/zero-width/whitespace rules rõ, operation hashes và profile/cache identity.
- Artifact JSON bất biến cả nested content, ID do host cấp riêng run; parent/
  child/ancestor/typed edges, import/export và hash kiểm tra mutation.
- Sensitivity/trust độc lập; normalize/derive không declassify hoặc tăng trust.
- 185 tests pass (53 mới), setup/Ruff/mypy 151 files pass; frozen seal còn nguyên.
- 1.650 checks trên 550 Dev texts (150 clean/400 attack+benign), ba profile.
  Raw/Unicode không đổi text nào trong corpus này; security đổi 80 text.
  Đây là số lượng biến đổi, không phải số tấn công bị chặn hoặc chất lượng model.

Primitives dùng S2/UNTRUSTED stress labels do QA tự gán, không suy ra từ GT và
không nhận đây là metadata mapping của benchmark. 50 robustness IDs đã khóa;
validator mới chỉ hash Test, không parse payload/GT. Không model/Broker run.

Còn phải làm:

1. ControlState/ContextBundle và Decision + Pre/Post/Final hooks pass-through.
2. Runtime mới theo version, source metadata host-owned, field-level sink arguments,
   model/context/ToolResult/final artifacts và trace v2. Giữ Broker cho mọi tool.
3. So A0 cũ/mới bằng cùng Replay: exact contexts, tool args/results, final và
   terminal behavior; không bật security normalization trong điều kiện raw A0.
4. 20 smoke, 20–30 clean Dev, 20–30 attack/benign Dev, retries/failures; kiểm tra
   lineage/sensitivity/trust thực và performance/memory overhead.
5. Receipt/full DoD và freeze nền tảng. Không sang Phase 5 trước nghiệm thu.

Không cần tài khoản/graph database/Kaggle cho các bước local này.
