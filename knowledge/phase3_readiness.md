# Phase 3: tiến độ theo Definition of Done

Cập nhật 2026-09-07 sau boundary batch. Theo yêu cầu owner
báo %: ước lượng **55–60% effort Phase 3**, không metric nghiệm thu. Cơ sở là
hạ tầng thực thi/QA đã có đáng kể và pool mở rộng, nhưng các deliverable
variants/split/freeze vẫn chưa đạt. Không có trọng số effort chốt trước nên
đây là khoảng ước lượng quản lý, không kết quả đo chính xác.

72 ca được lưu, giữ 70 đại diện sau hai quyết định gộp. Đủ 70/70 về số lượng
tạm giữ, không phải 100% family accepted hay Phase 3. Whole-pool admission có
thể gộp/thay thế thêm; chưa có bộ thay thế được duyệt/freeze. Draft v1 cũ không
tính vào dataset đạt chuẩn. Bước tới là review/chọn pool, không count-driven expansion.

| DoD trong Phase 3 | Bằng chứng hiện tại | Còn thiếu |
|---|---|---|
| 1. 70 canonical families | 72 working, 70 retained/2 merged, 20 review units | Quyết định admission toàn pool; đủ số chưa đủ acceptance |
| 2. Năm variants/family | Có helper cơ học và validator | Bộ 350 variants thay thế có QA |
| 3. Matched benign completeness | 72 cặp canonical dùng chung task/oracle trong mỗi pair | 350 benign variants đã kiểm tra |
| 4. Split 40/30 theo family | Có quy tắc và audit nhóm | Split mới hợp lệ, stratification |
| 5. Exact experimental counts | Mục tiêu đã khóa | Các tập 200/150 attack và benign đạt chuẩn |
| 6. Safe utility path | 288 standard = 256 reused + 32 fresh; thêm hai safe alternatives | Bao phủ toàn bộ benchmark và giới hạn utility còn lại |
| 7. Violation machine-checkable | Bounded projections/final-policy/quota/revocation, bên cạnh oracle cũ | Oracle phù hợp cho mọi canonical được chọn |
| 8. Semantic variant equivalence | Chưa có bộ mới được duyệt | Review đủ năm dạng của attack/benign |
| 9. Pair integrity | Hash-bound prior reviews và tám cặp mới; bounded QA | Quyết định release toàn pool và variant pair QA |
| 10. No Test tuning | Đang tuân thủ; không có LLM/Test run mới | Duy trì kỷ luật sau seal |
| 11. No real side effects | Mock tools qua Broker; test chặn mạng pass | Duy trì trên mọi overlay được bổ sung |
| 12. Reproducibility | Hash input/source/trace, Replay tái lập | Mapping/split/schema/version và release freeze toàn bộ |

Nguồn: [DoD chi tiết](../plan/phase3.md),
[phase status](../docs/project/phase_status.md),
[receipt boundary](../experiments/manifests/phase3_boundary_v1_validation01.json),
[tóm tắt review](../docs/benchmark/boundary_batch_summary.md).

Kiểm tra mới nhất: 466 tests pass (38 test mới), setup/Ruff/mypy 134 source
files pass; không thay scores Gemma/Qwen, không tính Replay thành ASR/FPR.
Lượt này thêm tám ứng viên; chưa tăng số family nghiệm thu.
Xem [handoff](handoff.md) cho bước thực hiện tiếp theo.
