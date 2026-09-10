# Context/policy GPU stress — continuation

2026-09-11: GPU version1 ERROR, một submission, giữ nguyên bằng chứng thất bại.
Nền native CPU đã accepted cho
library-only scope; [contract mới](../docs/architecture/phase5_context_policy_gpu_v1_contract.md).

Đã thêm hai JSON publisher metadata byte-identical với immutable inventory:
agent243bytes/repetition1.05; guard242bytes/repetition1.1. Agent metadata đọc từ
exactrevision HF bằng TLS; guard dùng acquisition cũ, không đọc/tải weights.
Auditor kết hợp23stress+10policy, bind full agent runtime digest và guard snapshot.
New outer auditor bind remote/bundle/80rawfiles; chưa có native stress artifacts.

Dispatcher mới giữ nguyên HF entry; stub dùng synthetic pair và4case policy
harness, không giả làm native GPU evidence.32-file standalone wrapper/builder
source-only local mount rehearsal đã có;45focused tests đạt, Ruff/mypy264 đạt.
Source `9bbf5eb` đã commit. [Exactpreflight](../experiments/manifests/phase5_context_policy_gpu_v1_preflight01.json)
đạt hai archive/expanded/PAX layouts:8tools/21Dummy/missing-only20retained,
6nativeprogress workers/layout, owner90/90/child0; dispatcher context+policy
stub đạt, metadata pin đạt. Không localweights/nativecontext.
[Pre-submit QA](../experiments/manifests/phase5_context_policy_gpu_v1_pre_submit_qa01.json):
full1.788pass/1optional skip370,00s, setup/Ruff/mypy264/knowledge đạt.
146frozen source/364historicalraw/32overlay/seals hash-only unchanged.
Current Kaggle GPU28,27h, Dataset11942593private/v1ready, modelversion1filelist
truy cập được, tên kernel mới chưa tồn tại lúc kiểm trước push. Báo cáo ngoài task giữ nguyên.

Source/QA đã push `b257506` trước một submission version1 kernel
`huylmhuhu/react-vn-context-policy-v1`/T4/timeout3600s; sau đó ERROR. Remote source
`build/kaggle/context_policy_gpu_v1_remote_source01` khớp exactwrapperSHA;
metadata private/offline/pinned image/modelv1 đúng.
[Submission](../experiments/manifests/phase5_context_policy_gpu_v1_submission01.json).
Đã tải đủ outputs vào `results/phase5_context_policy_gpu_v1_raw01`: 59 files,
không phải 80 files của successful path. [Failure receipt](../experiments/manifests/phase5_context_policy_gpu_v1_failure01.json)
bind raw/remote hashes và bằng chứng nguồn gốc. Agent load 259,04 giây, attempt
259,81 giây rồi BACKEND_FAILURE; guard chưa chạy, không READY/stress generation.
Summary actual_model_generation_calls là null, không sửa thành 0. Một TERMINATE,
không graceful; 6 VRAM recovery samples signed residual 0, không claim leak-free.

Nguyên nhân: policy factory v1 nhận ReadyBackend từ host ReadyFactory, vi phạm
exact native type admission. Stub preflight trước đó không chạy chuỗi factory
của HF entry. Bản sửa versioned giữ ReadyFactory ở ngoài cùng; CPU real-spawn
rehearsal tái hiện bản cũ lỗi và bản sửa READY cả hai roles, không model load.
[Contract v2](../docs/architecture/phase5_context_policy_gpu_v2_contract.md) bổ sung
factory control cho cả hai exact layouts trước GPU, giữ nguyên 32-file v1 overlay
và thêm 4 files. Chưa submit v2; tiếp full QA/commit/exact preflight/push/quota.
Không Test/privateGT hoặc localmodel. Không nguồn mới sửa trong gói đã gửi.

Sau gate này vẫn cần runtimeintegration, A4processing scope, finalentitlements,
grouped Dev decision/differential/freeze. Không lấy sốtestpass làm%Phase5.
