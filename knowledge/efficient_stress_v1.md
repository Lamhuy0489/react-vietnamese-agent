# Tích hợp attention vào bài thử model

2026-09-11. [Tensor gate đã đạt](sdpa_tensor_v1.md); owner yêu cầu làm luôn bước
tiếp theo. [Contract](../docs/architecture/phase5_efficient_stress_v1_contract.md)
là triển khai cụ thể từ design lịch sử, không sửa frozen files.

Đã có core single-use worker-local scope, factory/dispatcher, independent
attention auditor và outer source auditor, 42-file wrapper/builder mới. Giữ
ReadyFactory ngoài, policy/stress/native loaders cũ nguyên vẹn; chỉ bật HF
repeat_kv + forced efficient trong request rồi restore. Check từng attention
call và profile hai call/role để có actual dispatch evidence.

72 focused tests đạt (4,17s), gồm pinned HF source với fake Tensor trên đầy đủ
14.364/3.612 call sequences, có/không mask; không native tensor/model claim.
System Python diễn tập real-spawn mới: bản cũ BACKEND_FAILURE, bản mới READY
cả hai roles, không weights/stress consumed, handles reaped.
`results/phase5_efficient_factory_v1_rehearsal01` và dispatcher dev01 đã đạt;
các lượt này dùng working source chưa freeze, không phải exact release.
CLI lần đầu truyền commit thiếu ký tự bị từ chối trước writes, không inference.

Đang chạy full QA `results/phase5_efficient_stress_v1_pre_submit01_pytest.xml`.
Chưa commit source/exact preflight hoặc GPU submission mới ở mốc ghi này.
Tiếp freeze source, exact hai layouts trong clean worktree (giữ nguyên sửa đổi
ngoài task ở plan6–9), push source/QA, kiểm quota/pins rồi một kernel mới.
Không local model/Test/privateGT; không pending model/account access mới.
