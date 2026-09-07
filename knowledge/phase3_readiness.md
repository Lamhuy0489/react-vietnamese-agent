# Phase 3: nghiệm thu theo Definition of Done

Cập nhật 2026-09-07: **12/12 DoD đã đạt trong phạm vi benchmark synthetic và
owner self-review waiver; adversarial_v2 accepted và Test đã seal.**
Không dùng ước lượng effort 65–70% ở các ghi chú lịch sử làm trạng thái hiện hành.
Đây là hoàn thành Phase 3, không phải hoàn thành 100% đồ án.

| DoD | Bằng chứng |
|---|---|
| 1. Canonical families | 70 paired scenarios đã nhận, hai merge giữ làm lịch sử |
| 2. Năm variants/family | Năm dạng, 350 attack records |
| 3. Benign completeness | 350 benign, mỗi attack đúng một matched control |
| 4. Family split | 40 Dev/30 Test, 20 conservative groups không bị tách |
| 5. Experimental counts | Mỗi branch 200 Dev/150 Test, không cộng canonical |
| 6. Safe utility path | Safe references mọi canonical/variant và quota alternatives pass |
| 7. Machine-checkable violation | Frozen six-scorer adapter giữ final-policy/derived fields |
| 8. Semantic equivalence | 280 linguistic + 140 boundary self-review; 280 structural QA |
| 9. Pair integrity | Task/source/resources và family/group/split mapping kiểm tra đúng cặp |
| 10. No Test tuning | Không held-out model run; sau seal Dev loader không mở Test |
| 11. No side effects | Mọi tool qua Broker; network-interdiction tests pass |
| 12. Reproducibility | Source/config/environment/schema/mapping/payload hashes + archive + seal |

782 tests pass trước seal; hai seal-only tests skip. Sau seal 132 tests pass;
650 historical construction tests không collect trước import vì bảo vệ Test.
Setup/Ruff/mypy 146 files, clean và adversarial seals pass. 1.692 reference
paths tái chấm/archive là bằng chứng tái sử dụng, không inference mới.

[Nghiệm thu và giới hạn](../docs/benchmark/adversarial_release_v2_summary.md),
[receipt](../experiments/manifests/phase3_release_v2_closure.json),
[phase status](../docs/project/phase_status.md), [handoff](handoff.md).

Giới hạn không biến mất: self-review không independent human review; 70 scenario
families không phải 70 cơ chế độc lập; output-poisoning 12/3 do grouped split.
Phase 4 chưa bắt đầu và cần owner cho phép.
