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

Source `5267218` đã commit. FullQA1.931pass/1optional skip trong389,21s;
XML `results/phase5_efficient_stress_v1_pre_submit01_pytest.xml`, setup/Ruff/
mypy282/knowledge đạt. [QA](../experiments/manifests/phase5_efficient_stress_gpu_v1_pre_submit_qa01.json).
[Exact preflight](../experiments/manifests/phase5_efficient_stress_gpu_v1_preflight01.json)
42files/hai layouts archive/expandedPAX đạt; clean checkout
`/private/tmp/react-efficient-source.i4pHUV`, package dưới
`build/kaggle/phase5_efficient_stress_gpu_v1_preflight01/kernel` trong checkout đó.
106overlay entries/187raw lịch sử reverified; packaged45files/4knownsecrets/0matches.
Quota28,02h, Dataset11942593private/v1ready và model mountv1 đã kiểm.
Source/QA push `a66514e`; [một submission](../experiments/manifests/phase5_efficient_stress_gpu_v1_submission01.json)
version1 thành công, `huylmhuhu/react-vn-efficient-stress-v1`, lúc kiểm
2026-09-11 14:03:56 UTC. Đang theo dõi, chưa có kết luận model stress.
Không push lại. Pull source fresh, chờ terminal rồi tải toàn bộ outputs fresh
và audit hai lần; giữ nguyên source5267218 và package đã gửi.
Không local model/Test/privateGT; không pending model/account access mới.
