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
2026-09-11 14:03:56 UTC. Kernel đã COMPLETE, không còn job chạy.
[Báo cáo](../docs/evaluation/phase5_efficient_stress_gpu_v1_report.md),
[selected audit](../experiments/manifests/phase5_efficient_stress_gpu_v1_audit01.json):
90raw/2remote files, hai audits01/02 byte-identical. Native full-context gate đạt:
agent4096+512/cache4608, guard4096+128/cache4224, đủ28layers mỗi model.
Generation48,447s/6,085s; host48,664s/6,221s. Agent peakallocated10,408/5,077GiB;
guard3,248GiB, không OOM hoặc đổi caps. Timing có instrumentation, không speedup.
14.364/3.612attention calls, bốn actual efficient dispatch samples, policy và
bindings/flags restored. Hai TERM/-15/reaped,0graceful,6recovery samples residual0
haiGPU, không semaphore warning; không exhaustive IPC claim.
Raw `results/phase5_efficient_stress_gpu_v1_raw01`, remote
`build/kaggle/efficient_stress_gpu_v1_remote_source01`, giữ nguyên. Không submit lại.
Sau download rerun72focused đạt5,09s, setup/Ruff/mypy282 đạt; source/preQA hashes
kiểm lại. Chưa sửa source5267218 hoặc dùng treatment cho benchmark.

Tiếp runtime integration riêng: adapter attention nhiều request nhưng process-local,
không phụ thuộc geometry cố định/forced length của stress; ModelPair task-local,
A0–A6 isolation/parity/Broker/final/lifecycle, rồi A4/general final và grouped Dev.
Không cắm trực tiếp EfficientStressBackend single-use vào request ReAct bình thường.
Không local model/Test/privateGT; không pending model/account access mới.
