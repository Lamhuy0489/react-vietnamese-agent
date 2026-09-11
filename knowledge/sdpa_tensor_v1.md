# Phép thử attention không weights

2026-09-11: owner đã đồng ý tiếp tục phương án tối ưu attention sau OOM v2.
[Contract](../docs/architecture/phase5_sdpa_tensor_v1_contract.md).
Chỉ làm Phase5; không Test hoặc local model. Hai GPU runs v1/v2 cũ giữ nguyên.

Đã hoàn tất tensor runner/independent auditor,28-file wrapper và exact
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
Quota28,07h và Dataset11942593private/v1ready là kiểm tra trước submission.
Source/QA đã push `50a6092`; một kernel `huylmhuhu/react-vn-sdpa-tensor-v1`
version1 COMPLETE. [Báo cáo](../docs/evaluation/phase5_sdpa_tensor_gpu_v1_report.md),
[selected audit](../experiments/manifests/phase5_sdpa_tensor_gpu_v1_audit01.json):
59raw/2remote files, hai audits byte-identical;10fresh native processes,
14attention calls/0models. Candidate_valid=true, cả4parity đạt.
Long4096 agent native OOM dưới tensor-only2GiB, candidate120MiB peakallocated;
guard native1920,172MiB/candidate52MiB. Hai boundary decode đạt. Đã quan sát
native math và candidate efficient operators; không suy retrospectively nguyên
nhân OOM cũ hoặc công bố speedup từ timing có profiler/cold-start.

Raw `results/phase5_sdpa_tensor_gpu_v1_raw01`, remote
`build/kaggle/sdpa_tensor_gpu_v1_remote_source01`, audits01/02 ở results; giữ
nguyên. Không job Kaggle/local còn chạy. Chưa đổi model attention. Tiếp
[thiết kế tích hợp](../docs/architecture/phase5_efficient_stress_v1_design.md):
single-use worker-local scope, giữ ReadyFactory ngoài, audit restoration/masks/
dispatch rồi fullQA/exact package trước model GPU mới. Chưa triển khai bước này.

Thành công tensor không thay thế full4096+512/128 model stress hoặc Phase5
acceptance; cần runtime integration/A4/general final/grouped Dev/freeze sau đó.
