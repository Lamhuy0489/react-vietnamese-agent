# Trạng thái hiện tại

Cập nhật: 2026-09-13. **Phase 5 đang làm, chưa nghiệm thu.**

## Hiện hành — sửa lỗi sau audit

Mốc mới nhất là [ModelPair/runtime v7 bounded CPU integration](phase5_pair_runtime_v1.md):
A0/A1 chỉ agent, A2–A6 hai worker sibling qua parent role adapters. Đã tách schema
pair và host proposals khỏi transport attempts. CPU02 có 52 focused tests,
full QA **2.496 pass/1 skip** (477,43s), 51 joined receipts, 441 source/530 raw
hashes khớp và 169 tracked data hashes không đổi. CPU01 giữ làm lịch sử, không
selected acceptance vì schema trace cũ sai. Không có GPU run mới; xem [handoff](handoff.md).

Bản phát triển mới là `security_runtime_v7`, đi với final entitlement v2,
processing scope v2 và typed value origin v2. Không dùng v1 entitlement/runtime v6
cho thí nghiệm mới: audit phát hiện cấp quyền chéo, supplied-grant validation yếu,
bỏ sót bản zero-width đi kèm raw và metadata A0 tự nhận policy A6.

V7 ghép bounded A4 scope trước Broker ở A4–A6; giữ scope theo task, ghi trace
và không đổi prompt/tools/decoding. Kiểm thực tế database smoke còn phát hiện
synthetic ID bị bộ origin v1 bỏ qua; v2 bổ sung profile có giới hạn.

91 focused tests pass; full QA **2.444 pass/1 native-tqdm skip** trong 460 giây.
Setup/Ruff/mypy 314 files/knowledge đạt. Receipt được audit độc lập:
436 source/573 raw hashes khớp, 169 tracked data hashes không đổi.
[Receipt](../experiments/manifests/phase5_remediation_v2_cpu01.json) là working-tree
CPU QA, không gọi là clean release; xem [handoff](handoff.md).
[Chi tiết sửa lỗi và bằng chứng](phase5_remediation_v2.md).

## Bằng chứng cần phân biệt

- Entitlement v1 selected receipt có hash `pytest.log` sai: giữ nguyên để audit,
  rút lại việc coi receipt này là bằng chứng toàn vẹn.
- Runtime v6 raw hashes khớp nhưng test cũ không bao phủ các lỗi hành vi đã tìm ra.
- Native Qwen 7B/1.5B trên T4×2 đã chạy 6 calls kỹ thuật; đó không phải benchmark
  chất lượng guard/ASR/utility. Worker cleanup cũ là forced, không graceful.
- Phase 1, clean_v1.1 Phase 2, adversarial_v2 Phase 3 và Phase 4 đã được nghiệm thu
  theo phạm vi/owner waiver ghi trong phase status. Không mở lại Test để tuning.

## Các gate còn mở

1. Native ModelPair/runtime packaging và GPU lifecycle; CPU integration đã đạt
   phạm vi kiểm thử đã ghi, chưa chứng nhận mọi native failure/timing condition.
2. Production guard quality và grouped Dev differential validation.
3. Broader semantic origin/scope coverage và formal Phase 5 freeze.

Không lấy số test pass làm phần trăm hoàn thành. Không chuyển Phase 6/7.
[Tiến độ/gate](phase5_progress.md) · [Chỉ mục tri thức](README.md).
