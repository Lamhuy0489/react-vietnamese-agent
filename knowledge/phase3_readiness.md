# Phase 3: tiến độ theo Definition of Done

Cập nhật 2026-09-06 sau pilot revision v2.2. Ước lượng quản lý công việc:
**khoảng 25–30%**, không phải metric nghiệm thu hoặc phần trăm checklist pass.
Lý do: specification, schema và hạ tầng thực thi đã có phần đáng kể; canonical
mới ở pilot, còn bộ variants, semantic QA toàn bộ, split và freeze chưa hoàn tất.
Không có trọng số effort được chốt trước, nên không đưa số chính xác giả tạo.

12/70 = khoảng 17% **số cặp ứng viên so với mục tiêu**, không phải 17% family đã
accepted. Chưa có bộ canonical thay thế được duyệt/freeze; draft 70 family v1
cũ bị từ chối ở audit, không cộng vào tiến độ dataset đạt chuẩn.

| DoD trong Phase 3 | Bằng chứng hiện tại | Còn thiếu |
|---|---|---|
| 1. 70 canonical families | 12 ứng viên revised executable, bảy review units tạm thời | Độc lập ngữ nghĩa và đủ 70 family |
| 2. Năm variants/family | Có helper cơ học và validator | Bộ 350 variants thay thế có QA |
| 3. Matched benign completeness | 12 cặp canonical dùng chung task/oracle | 350 benign variants đã kiểm tra |
| 4. Split 40/30 theo family | Có quy tắc và audit nhóm | Split mới hợp lệ, stratification |
| 5. Exact experimental counts | Mục tiêu đã khóa | Các tập 200/150 attack và benign đạt chuẩn |
| 6. Safe utility path | 48 Replay; 24 safe đạt utility kiểu dữ liệu + evidence | Bao phủ toàn bộ benchmark và giới hạn utility còn lại |
| 7. Violation machine-checkable | Scope/read/sink/final QA trên 12 ứng viên | Oracle cho mọi cơ chế được author thêm |
| 8. Semantic variant equivalence | Chưa có bộ mới được duyệt | Review đủ năm dạng của attack/benign |
| 9. Pair integrity | v2.2 sửa neutral wording/độ dài, giữ mục tiêu và bằng chứng | Pair QA toàn bộ pool và các giới hạn còn lại |
| 10. No Test tuning | Đang tuân thủ; không có LLM/Test run mới | Duy trì kỷ luật sau seal |
| 11. No real side effects | Mock tools qua Broker; test chặn mạng pass | Duy trì trên mọi overlay được bổ sung |
| 12. Reproducibility | Hash input/source/trace, Replay tái lập | Mapping/split/schema/version và release freeze toàn bộ |

Nguồn: [DoD chi tiết](../plan/phase3.md),
[phase status](../docs/project/phase_status.md),
[receipt revision QA](../experiments/manifests/phase3_canonical_revision_v22_validation01.json),
[tóm tắt revision](../docs/benchmark/canonical_revision_summary.md).

Kiểm tra mới nhất: 244 tests pass (24 test revision mới), setup/Ruff/mypy 112 source
files pass; không thay scores Gemma/Qwen, không tính Replay thành ASR/FPR.
Lượt này cải thiện pilot paired data chứ không tăng số family đã nghiệm thu.
Xem [handoff](handoff.md) cho bước thực hiện tiếp theo.
