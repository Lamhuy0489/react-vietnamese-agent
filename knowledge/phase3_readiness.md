# Phase 3: tiến độ theo Definition of Done

Cập nhật 2026-09-07 sau whole-pool admission/grouped split. Ước lượng
**65–70% effort Phase 3**, không metric nghiệm thu. Không có trọng số effort
khóa trước nên đây là khoảng quản lý, không kết quả đo khoa học.

70 canonical đã nhận **cho authoring biến thể**, 40 Dev/30 Test, giữ 20 nhóm.
Không phải 70 abstract mechanisms độc lập hoặc 100% Phase 3. Còn bộ 350+350
variants có review/QA, release integration và Test seal. Draft v1 không tính.

| DoD trong Phase 3 | Bằng chứng hiện tại | Còn thiếu |
|---|---|---|
| 1. 70 canonical families | Whole-pool rationale, 70 selected/2 merged | Đưa selection vào executable variant release |
| 2. Năm variants/family | Helper cơ học đã có | Bộ 350 variants thay thế có QA |
| 3. Matched benign completeness | 70 selected canonical pairs | 350 benign variants đã review |
| 4. Split 40/30 theo family | Exact grouped split, 20 nhóm, seed/objective/strata báo cáo | Giữ mapping qua variants; lệch output 12/3 phải công bố |
| 5. Exact experimental counts | Canonical/pair/split identities pass | 200/150 variants cho mỗi attack/benign |
| 6. Safe utility path | 280 selected reference paths trong 288 stored records | Replay với overlay biến thể, không chỉ canonical |
| 7. Violation machine-checkable | Oracle từng batch có bounded QA | Adapter release giữ đủ final-policy/derived fields |
| 8. Semantic variant equivalence | Chưa có bộ variants mới được duyệt | Review năm dạng attack/benign |
| 9. Pair integrity | Whole-pool self-review dưới owner waiver | Variant equivalence và pair QA |
| 10. No Test tuning | Không LLM/Test run mới; Test chưa seal | Duy trì sau assignment/seal |
| 11. No real side effects | Mock Broker và offline tests pass | Giữ trên mọi overlay biến thể |
| 12. Reproducibility | Selection manifest, evidence/source/input hashes | Release mapping/schema/inventory và immutable seal |

Nguồn: [DoD chi tiết](../plan/phase3.md),
[phase status](../docs/project/phase_status.md),
[selection receipt](../experiments/manifests/phase3_canonical_selection_v1_validation01.json),
[tóm tắt/giới hạn](../docs/benchmark/canonical_selection_summary.md).

495 tests pass (29 mới), setup/Ruff/mypy 136 source files và clean seal pass.
Không có Replay/model run mới; tái kiểm tra bằng chứng cũ, không tăng số lần
thực nghiệm hay thay điểm Gemma/Qwen. [Handoff](handoff.md) ghi bước tiếp theo:
author variants theo assignment đã chốt, không thêm ca hoặc resplit.
