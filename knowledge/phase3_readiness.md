# Phase 3: tiến độ theo Definition of Done

Cập nhật 2026-09-07 sau 12 task-effect pairs. Theo yêu cầu owner
báo %: ước lượng **50–55% effort Phase 3**, không metric nghiệm thu. Cơ sở là
hạ tầng thực thi/QA đã có đáng kể và pool mở rộng, nhưng các deliverable
variants/split/freeze vẫn chưa đạt. Không có trọng số effort chốt trước nên
đây là khoảng ước lượng quản lý, không kết quả đo chính xác.

64 ca được lưu nhưng chỉ giữ 62 đại diện sau hai quyết định gộp. 62/70 ≈ 89%
là số đại diện tạm giữ so với mục tiêu, không phải tỷ lệ family accepted.
Cần thêm ít nhất tám; lựa chọn toàn pool vẫn có thể gộp thêm. Chưa có bộ thay
thế được duyệt/freeze; draft 70 family v1 cũ không tính vào dataset đạt chuẩn.

| DoD trong Phase 3 | Bằng chứng hiện tại | Còn thiếu |
|---|---|---|
| 1. 70 canonical families | 64 working, 62 retained/2 merged, 17 review units | Ít nhất tám đại diện nữa và quyết định release để đạt 70 |
| 2. Năm variants/family | Có helper cơ học và validator | Bộ 350 variants thay thế có QA |
| 3. Matched benign completeness | 64 cặp canonical dùng chung task/oracle trong mỗi pair | 350 benign variants đã kiểm tra |
| 4. Split 40/30 theo family | Có quy tắc và audit nhóm | Split mới hợp lệ, stratification |
| 5. Exact experimental counts | Mục tiêu đã khóa | Các tập 200/150 attack và benign đạt chuẩn |
| 6. Safe utility path | 256 standard paths = 208 reused + 48 fresh; 128 safe | Bao phủ toàn bộ benchmark và giới hạn utility còn lại |
| 7. Violation machine-checkable | Các oracle bounded; thêm query và exact two-piece coverage | Oracle phù hợp cho mọi canonical được chọn |
| 8. Semantic variant equivalence | Chưa có bộ mới được duyệt | Review đủ năm dạng của attack/benign |
| 9. Pair integrity | Hash-bound prior reviews và 12 cặp mới; bounded QA | Quyết định release toàn pool và variant pair QA |
| 10. No Test tuning | Đang tuân thủ; không có LLM/Test run mới | Duy trì kỷ luật sau seal |
| 11. No real side effects | Mock tools qua Broker; test chặn mạng pass | Duy trì trên mọi overlay được bổ sung |
| 12. Reproducibility | Hash input/source/trace, Replay tái lập | Mapping/split/schema/version và release freeze toàn bộ |

Nguồn: [DoD chi tiết](../plan/phase3.md),
[phase status](../docs/project/phase_status.md),
[receipt completion-authoring](../experiments/manifests/phase3_completion_v1_validation01.json),
[tóm tắt review](../docs/benchmark/completion_batch_summary.md).

Kiểm tra mới nhất: 428 tests pass (27 test mới), setup/Ruff/mypy 131 source
files pass; không thay scores Gemma/Qwen, không tính Replay thành ASR/FPR.
Lượt này thêm 12 ứng viên; chưa tăng số family nghiệm thu.
Xem [handoff](handoff.md) cho bước thực hiện tiếp theo.
