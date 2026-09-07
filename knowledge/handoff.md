# Bàn giao phiên làm việc

Cập nhật: 2026-09-08. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **A6 value-origin và final-release components đã qua synthetic QA**.
Source `3b9f565`, [contract](../docs/architecture/phase5_value_origin_contract.md),
[selected receipt](../experiments/manifests/phase5_value_origin_v1_validation01.json),
[tiến độ](phase5_progress.md). Selected từ source sạch khớp stable preflight;
130 source/101 raw hashes đã kiểm lại. Phase 1–4 accepted; Phase 5 chưa nghiệm thu.

Index chỉ nhận raw USER/tool-source roots do host quan sát, match theo kiểu dữ liệu
và giữ mọi origin cùng sensitivity/trust độc lập. Final-release component tạo
artifact mới bằng ALLOW/REDACT/DENY tất định, không sửa raw/proposed hoặc hạ nhãn.
Đã sửa nguồn có transformation lọt admission và protected value chuẩn hóa thành
rỗng gây crash. A6 chưa operational: runtime v3 vẫn A0–A5, Final pass-through.

## Bước tiếp theo

1. Đọc phase status/contract, kiểm tra Git và dùng validator value-origin mới trong
   [runbook](runbook.md). Không sửa source/test/config/contract đã ghi receipt;
   thêm version/module riêng cho bước tích hợp tiếp theo.
2. Freeze contract A6 runtime trước triển khai: PreGate critical-field origin và
   unknown-deny, PostGate safe context views, FinalGate trả released content;
   authorization cho final phải từ host policy/user, không evaluator GT.
   Cần arbitration riêng cho coarse A3–A5 veto để giữ benign utility khi có nguồn
   public đủ evidence; whole-context lineage không chứng minh nguồn từng token.
3. Chốt guard model/revision chung A2–A6 và lifecycle process-owned GPU hiệu quả.
   Adapter hiện cold-load mỗi cache miss, không phải persistent GPU worker hoặc
   bằng chứng hiệu suất model. Không cần tài khoản mới cho local implementation.
4. Rà A4 general processing scope ngoài external anchors; chốt grouped Dev
   tune/validation protocol trước tuning. Không load Test/authoring payload,
   thay seal/frozen source hoặc sang Phase 6.
5. Meta access vẫn thiếu cho Llama pilot riêng; không chặn local A6 work.

## Bằng chứng

- Preflight và selected reproduction đều **696 tests pass**, 103 mới;
  setup/Ruff/mypy 183 files/knowledge pass. 24 synthetic component conditions:
  12 ALLOW, 8 REDACT, 4 DENY. Zero fresh Replay/guard classifications/model runs;
  không ASR/utility claim. 641 prior source entries nguyên vẹn.
- 130 source/101 raw hashes của selected receipt đã kiểm lại; stable summary
  khớp preflight. Kiểm tra riêng serialized artifacts của 24 ca đối chiếu
  IDs/hashes/labels/origin/proposed/released và nội dung DENY rỗng.
- Tests có typed values/DB columns-rows, nguồn trùng public/protected, numeric
  equivalence/boundaries/common values, raw-user presence không tự cấp quyền,
  admission atomic/fresh/monotone, resource limits, deterministic redaction,
  normalized-only detection, replacement collision và artifact round-trip.
- Mốc session trước: source `8a4ca3d`,
  [receipt](../experiments/manifests/phase5_session_v1_validation01.json),
  593 tests, 44 A0–A2 parity pairs + 30 session cases = 118 Replay;
  165 fake guard classifications, 225 snapshots, 15 expected denials.

## Giới hạn

ALLOW chỉ có nghĩa không khớp profile hữu hạn, không chứng minh không có rò rỉ.
Chưa hỗ trợ leakage paraphrase/encoded/translated tổng quát, short names,
unlabelled integral numbers hoặc SQL alias semantics. Normalization chỉ phục vụ
phát hiện, không authorize destination. Default final component clearance S0
chặn S1/S2 match; quyền final hợp lệ và unknown critical relations còn cần policy.

Chưa guard LLM thật, benchmark Dev tuning hoặc Test payload parsing; seal checks
chỉ hash/metadata. Runtime A6, Post views và full FinalGate chưa tích hợp.
A0–A5 và điểm pilot cũ giữ nguyên. Assistant self-review theo owner waiver,
không independent human review. Không credentials/private GT/Test payload/CoT
trong knowledge; không có pending access cho công việc local tiếp theo.
