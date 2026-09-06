# Phase 3: tiến độ theo Definition of Done

Cập nhật 2026-09-06 sau transaction batch và unified QA v2. Theo yêu cầu owner
báo %: ước lượng **40–45% effort Phase 3**, không metric nghiệm thu. Cơ sở là
hạ tầng thực thi/QA đã có đáng kể và pool mở rộng, nhưng các deliverable
variants/split/freeze vẫn chưa đạt. Không có trọng số effort chốt trước nên
đây là khoảng ước lượng quản lý, không kết quả đo chính xác.

40/70 ≈ 57% **số cặp ứng viên so với mục tiêu**, không phải 57% family đã
accepted. Chưa có bộ canonical thay thế được duyệt/freeze; draft 70 family v1
cũ bị từ chối ở audit, không cộng vào tiến độ dataset đạt chuẩn.

| DoD trong Phase 3 | Bằng chứng hiện tại | Còn thiếu |
|---|---|---|
| 1. 70 canonical families | 40 ứng viên executable, 15 review units, author self-review | Đủ pool và quyết định nhận/gộp để đạt 70 family |
| 2. Năm variants/family | Có helper cơ học và validator | Bộ 350 variants thay thế có QA |
| 3. Matched benign completeness | 40 cặp canonical dùng chung task/oracle trong mỗi pair | 350 benign variants đã kiểm tra |
| 4. Split 40/30 theo family | Có quy tắc và audit nhóm | Split mới hợp lệ, stratification |
| 5. Exact experimental counts | Mục tiêu đã khóa | Các tập 200/150 attack và benign đạt chuẩn |
| 6. Safe utility path | 160 fresh reference QA paths; 80 safe có utility/evidence | Bao phủ toàn bộ benchmark và giới hạn utility còn lại |
| 7. Violation machine-checkable | Scope/sink/final, argument/quota/prerequisite, complete Base64/hex và bounded row SQL | Oracle phù hợp cho mọi canonical được chọn |
| 8. Semantic variant equivalence | Chưa có bộ mới được duyệt | Review đủ năm dạng của attack/benign |
| 9. Pair integrity | Self-review 28 cặp trước và 12 cặp mới; bounded length/fixture QA | Quyết định release toàn pool và variant pair QA |
| 10. No Test tuning | Đang tuân thủ; không có LLM/Test run mới | Duy trì kỷ luật sau seal |
| 11. No real side effects | Mock tools qua Broker; test chặn mạng pass | Duy trì trên mọi overlay được bổ sung |
| 12. Reproducibility | Hash input/source/trace, Replay tái lập | Mapping/split/schema/version và release freeze toàn bộ |

Nguồn: [DoD chi tiết](../plan/phase3.md),
[phase status](../docs/project/phase_status.md),
[receipt tổng hợp v2](../experiments/manifests/phase3_pool_v2_validation01.json),
[tóm tắt batch](../docs/benchmark/transaction_batch_summary.md).

Kiểm tra mới nhất: 321 tests pass (24 test batch mới), setup/Ruff/mypy 121 source
files pass; không thay scores Gemma/Qwen, không tính Replay thành ASR/FPR.
Lượt này thêm 12 ứng viên/một nhóm mới và QA tổng hợp, chưa tăng family nghiệm thu.
Xem [handoff](handoff.md) cho bước thực hiện tiếp theo.
