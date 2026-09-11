# Phép thử attention không weights

2026-09-11: owner đã đồng ý tiếp tục phương án tối ưu attention sau OOM v2.
[Contract](../docs/architecture/phase5_sdpa_tensor_v1_contract.md).
Chỉ làm Phase5; không Test hoặc local model. Hai GPU runs v1/v2 cũ giữ nguyên.

Đang triển khai tensor runner/independent auditor,28-file wrapper và exact
preflight. Mỗi role có short prefill/decode parity, long4096 baseline/candidate
và boundary decode;10fresh native processes, cap2GiB dành riêng tensor.
Source `5aabea0` đã commit.34focused tests, full1.859pass/1optional skip trong
379,56 giây; setup/Ruff/mypy275/knowledge đạt. [Pre-submit QA](../experiments/manifests/phase5_sdpa_tensor_gpu_v1_pre_submit_qa01.json).
Exact28file preflight cả hai layouts đạt:8tools/21Dummy/resume/20retained,
6nativeprogress workers/layout và tensor stub10cases, không native tensor claim.
[Preflight](../experiments/manifests/phase5_sdpa_tensor_gpu_v1_preflight01.json).

Trong phiên xuất hiện thay đổi ngoài task ở plan/phase6–9; giữ nguyên và không
commit. Exact preflight dùng detached clean checkout `/private/tmp/react-sdpa-source.ZZCt8Y`
ở source5aabea0, package nằm dưới `build/kaggle/phase5_sdpa_tensor_gpu_v1_preflight01`.
Full pytest chạy ở workspace gốc; packaged source hashes kiểm riêng và khớp.
146frozen source entries/492raw lịch sử/seals hash-only nguyên vẹn.
Quota28,07h, Dataset11942593private/v1ready, tên kernel mới chưa tồn tại.
Chưa native kết quả hoặc đổi model attention; tiếp push QA rồi một submission.

Thành công tensor không thay thế full4096+512/128 model stress hoặc Phase5
acceptance; cần runtime integration/A4/general final/grouped Dev/freeze sau đó.
