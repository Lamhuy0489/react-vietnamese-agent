# Bàn giao phiên làm việc

Cập nhật: 2026-09-07. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

**Phase 4 đã được owner cho phép**, đang ở mốc primitive foundation. Phase 1,
Phase 2 clean_v1.1, Phase 3 adversarial_v2 đã accepted; Test vẫn khóa.
[Tiến độ Phase 4](phase4_progress.md),
[contract](../docs/architecture/phase4_foundation_contract.md).

Đã thêm normalizer raw/Unicode/security có phiên bản, immutable JSON artifacts,
run-isolated store, typed provenance DAG, ancestor queries, import/export và
sensitivity/trust joins độc lập. Đây chưa phải runtime có provenance hoàn chỉnh.
Không sửa source/data/scorer cũ, không bật defense trong A0.

## Bước tiếp theo

1. Xác nhận Git/remote và [phase status](../docs/project/phase_status.md);
   chạy setup/Ruff/mypy/pytest/knowledge-check theo [runbook](runbook.md).
2. **Triển khai ControlState/ContextBundle và Decision + Pre/Post/Final hooks
   pass-through**, đọc các mục XXXIV–LI của [phase4](../plan/phase4.md).
3. Thêm runtime version riêng, giữ frozen runtime A0 để so sánh. Artifact hóa
   user/model/arguments/ToolResult/final và context lineage; mọi tool qua Broker.
   Host-owned source metadata, không dùng evaluator GT để gán labels.
4. Mở rộng QA: cùng Replay so exact contexts/actions/results/final/terminal
   A0 cũ và mới; 20 smoke, 20–30 clean Dev, 20–30 adversarial Dev; retries/errors.
   Thêm trace v2, source/environment hashes, performance và memory diagnostics.
5. Chỉ sau đủ DoD mới nghiệm thu Phase 4. Không triển khai chặn A1–A6/Phase 5.
   Không dùng Test hoặc thay normalized profile dựa trên Test. Không gỡ seal.
6. Không cần tài khoản mới, graph database hoặc Kaggle cho phần local này.
   Meta access còn thiếu chỉ ảnh hưởng Llama pilot, không chặn Phase 4.

## Bằng chứng

- Source `a4e9a87`, [receipt](../experiments/manifests/phase4_primitives_v1_validation01.json):
  selected run khớp stable summary preflight, source hashes đúng. Quét bốn
  credential values trên 16 file trước commit: 0 match; knowledge-check pass.

- **185 tests pass**, gồm 53 tests mới. Setup/Ruff/mypy **151 files** pass.
- Primitive Dev QA: 150 clean instructions + 400 adversarial payloads × ba
  profiles = **1.650 checks**. Determinism/idempotence/raw preservation, labels
  và artifact serialization/lineage pass; không model hoặc Broker run.
- Trong corpus Dev: raw/Unicode có 0 text đổi; security có 80 text đổi. Đây là
  số biến đổi, không ASR, không tuyên bố ngăn tấn công. Stress labels S2/UNTRUSTED
  do QA chủ động gán, không phải benchmark source annotation.
- Validator mới parse 0 Test payload/GT; kiểm tra hash dependencies và đúng 50
  robustness IDs đã seal. Adversarial seal check vẫn pass. Các source/data cũ
  không bị sửa theo Git diff. Unicode profiles có golden tests gồm dấu tách,
  zero-width/combining adjacency, emoji, newline/paragraph separator, URL/email.
- Phase 3 closure source `c228a68`, evidence commit `a5547f9`:
  [receipt](../experiments/manifests/phase3_release_v2_closure.json).
  782 tests trước seal; 132 sau seal và 650 construction tests không collect.
  Không rerun các test construction đó trong phase sau.
- Model scores trước đây giữ nguyên: Gemma 6/21, Qwen7B 3/21 Dev.

## Giới hạn

Mốc primitive không chứng minh A0 parity/runtime lineage: phải làm tiếp.
NFKC/zero-width có thể đổi emoji joiner hoặc compatibility literals; normalized
view là tùy chọn, raw vẫn authoritative. Không tự sửa dấu/dịch/paraphrase.
Conservative provenance không phải token-level causal attribution.
Review theo owner waiver, không giả independent human review.
Không lưu credentials, GT, payload Test hoặc CoT trong knowledge.
