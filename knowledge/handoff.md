# Bàn giao phiên làm việc

Cập nhật: 2026-09-07. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

**Phase 4 đã được owner cho phép**, đã tích hợp runtime và kiểm tra A0 parity. Phase 1,
Phase 2 clean_v1.1, Phase 3 adversarial_v2 đã accepted; Test vẫn khóa.
[Tiến độ Phase 4](phase4_progress.md),
[contract runtime](../docs/architecture/phase4_runtime_contract.md).

Runtime version riêng đã có ControlState/ContextBundle, Pre/Post/Final hooks
pass-through, source snapshots, argument/field artifacts, context/model/final
lineage, trace v2 và audit-normalized views không đưa vào prompt. Mọi tool vẫn
qua Broker. Giữ raw A0 và source/data/scorer đã khóa, không bật defense.

## Bước tiếp theo

1. Xác nhận Git/remote và [phase status](../docs/project/phase_status.md);
   chạy setup/Ruff/mypy/pytest/knowledge-check theo [runbook](runbook.md).
2. **Rà metadata nguồn/search và propagation** theo các mục XXXIV–LI của
   [phase4](../plan/phase4.md); thay fallback bảo thủ bằng host-owned bindings
   khi có bằng chứng nguồn. Không suy labels từ payload hoặc evaluator GT.
3. Mở rộng sensitive/multi-step Dev trajectories để kiểm tra sink fields,
   final-answer lineage và search summaries. Suite hiện có 24 public Dev source
   probes, không phải adversarial utility/ASR evaluation hoàn chỉnh.
4. Đo overhead thời gian/bộ nhớ có kiểm soát với warm-up, repeats và môi trường
   được ghi nhận. Timing từng ca trong receipt chỉ là CPU Replay diagnostic.
   Source a65bc53 đã hash: thay đổi hành vi cần version mới, không sửa receipt.
5. Chỉ sau đủ DoD mới nghiệm thu Phase 4. Không triển khai chặn A1–A6/Phase 5.
   Không dùng Test hoặc thay normalized profile dựa trên Test. Không gỡ seal.
6. Không cần tài khoản mới, graph database hoặc Kaggle cho phần local này.
   Meta access còn thiếu chỉ ảnh hưởng Llama pilot, không chặn Phase 4.

## Bằng chứng

- Runtime source `a65bc53`,
  [receipt](../experiments/manifests/phase4_runtime_v1_validation01.json):
  **65 paired conditions / 130 fresh Replay** = 20 smoke + 21 clean Dev + 24
  attack/benign Dev probes. Exact context/action/result/final/terminal parity;
  824 artifacts, 1.173 edges, 390 raw file hashes. Stable summary khớp preflight.
- **224 tests pass**, gồm 39 tests runtime mới; setup/Ruff/mypy **156 files**
  và adversarial seal check pass. Clean Dev reference actions/faults chỉ dùng
  trong QA; runtime/catalog/prompt không nhận GT. Suite mới parse 0 Test payload,
  không LLM/Kaggle run. Còn thiếu metadata/search audit, controlled overhead và
  acceptance review; receipt ghi rõ `phase4_accepted: false`.
- Các số bên dưới là bằng chứng primitive/Phase 3 lịch sử.

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

Replay parity chứng minh plumbing trên các ca đã chạy, không chứng minh model
utility, ASR hay security defense. Metadata fallback còn coarse và bảo thủ.
NFKC/zero-width có thể đổi emoji joiner hoặc compatibility literals; normalized
view là tùy chọn, raw vẫn authoritative. Không tự sửa dấu/dịch/paraphrase.
Conservative provenance không phải token-level causal attribution.
Review theo owner waiver, không giả independent human review.
Không lưu credentials, GT, payload Test hoặc CoT trong knowledge.
