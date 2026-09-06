# Phase 3: tiến độ theo Definition of Done

Cập nhật 2026-09-06 sau linked-scope và unified QA. Chuyển sang theo dõi gate
và số lượng có bằng chứng; không cập nhật một % effort chính xác khi chưa có
trọng số. Ước lượng 30–35% của mốc trước là lịch sử, không metric nghiệm thu.

28/70 = 40% **số cặp ứng viên so với mục tiêu**, không phải 40% family đã
accepted. Chưa có bộ canonical thay thế được duyệt/freeze; draft 70 family v1
cũ bị từ chối ở audit, không cộng vào tiến độ dataset đạt chuẩn.

| DoD trong Phase 3 | Bằng chứng hiện tại | Còn thiếu |
|---|---|---|
| 1. 70 canonical families | 28 ứng viên executable, 14 review units tạm thời | Canonical distinctions được review và đủ 70 family |
| 2. Năm variants/family | Có helper cơ học và validator | Bộ 350 variants thay thế có QA |
| 3. Matched benign completeness | 28 cặp canonical dùng chung task/oracle trong mỗi pair | 350 benign variants đã kiểm tra |
| 4. Split 40/30 theo family | Có quy tắc và audit nhóm | Split mới hợp lệ, stratification |
| 5. Exact experimental counts | Mục tiêu đã khóa | Các tập 200/150 attack và benign đạt chuẩn |
| 6. Safe utility path | 112 fresh reference QA paths; 56 safe có utility/evidence | Bao phủ toàn bộ benchmark và giới hạn utility còn lại |
| 7. Violation machine-checkable | Scope/sink/final, argument/quota/prerequisite, complete Base64/hex và bounded row SQL | Oracle phù hợp cho mọi canonical được chọn |
| 8. Semantic variant equivalence | Chưa có bộ mới được duyệt | Review đủ năm dạng của attack/benign |
| 9. Pair integrity | v2.2 sửa neutral wording/độ dài, giữ mục tiêu và bằng chứng | Pair QA toàn bộ pool và các giới hạn còn lại |
| 10. No Test tuning | Đang tuân thủ; không có LLM/Test run mới | Duy trì kỷ luật sau seal |
| 11. No real side effects | Mock tools qua Broker; test chặn mạng pass | Duy trì trên mọi overlay được bổ sung |
| 12. Reproducibility | Hash input/source/trace, Replay tái lập | Mapping/split/schema/version và release freeze toàn bộ |

Nguồn: [DoD chi tiết](../plan/phase3.md),
[phase status](../docs/project/phase_status.md),
[receipt tổng hợp](../experiments/manifests/phase3_pool_v1_validation01.json),
[tóm tắt batch](../docs/benchmark/linked_scope_summary.md).

Kiểm tra mới nhất: 297 tests pass (34 test batch mới), setup/Ruff/mypy 119 source
files pass; không thay scores Gemma/Qwen, không tính Replay thành ASR/FPR.
Lượt này thêm tám ứng viên/hai nhóm mới và QA tổng hợp, chưa tăng family nghiệm thu.
Xem [handoff](handoff.md) cho bước thực hiện tiếp theo.
