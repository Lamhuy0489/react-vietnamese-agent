# Native policy library compatibility — CPU worker

Một CPU kernel version1 COMPLETE, một submission2026-09-10. Native4cases đạt,
68rawfiles/hai audits byte-identical; chỉ library execution, không model/GPU.
[Báo cáo](../docs/evaluation/phase5_policy_native_cpu_v1_report.md),
[audit](../experiments/manifests/phase5_policy_native_cpu_v1_audit01.json),
[submission](../experiments/manifests/phase5_policy_native_cpu_v1_submission01.json).
GitHub source/QA `c3bf60f` đã push trước submit.
Source worker `5c0c20e` đã chốt. [Exact preflight](../experiments/manifests/phase5_policy_native_cpu_v1_preflight01.json)
đạt cả archive/expanded/PAX:8tools/21Dummy,20retained checkpoints/missing-only
resume;6native progress workers/layout,owner90/90,child registrations0; stub
policy harness4cases/layout đạt. Không native Transformers/model ở local.
25tests mới (11harness/package+14audit) đạt; fullQApre02:1.734pass/1optional
skip trong370,38s, setup/Ruff/mypy260/knowledge đạt.
[Pre-submit QA](../experiments/manifests/phase5_policy_native_cpu_v1_pre_submit_qa01.json)
ghi hashes nguồn và JUnit, chưa phải bằng chứng native execution.
Lượt fullQApre01 bị mất tiến trình khi phiên tool ngắt, chưa có JUnit, không
tính pass; giữ nguyên `build/pytest_policy_native_cpu_v1_pre01` để đối chiếu.
Dataset11942593 vẫn private/v1/ready; tên kernel mới chưa trùng. Quota kiểm
2026-09-10:GPU28,27h còn, không reservation; run nàyCPU không dùng GPU.
Local system Torch2.2.2 không dùng thay pinned Kaggle Torch2.10.0+cu128 và
Transformers5.5.0. KernelCPU riêng, private/offline, no model_sources/GPU/TPU.
Không materialize `guard-model.tar` hoặc tải/load weights. Dataset cũ giữ nguyên.

Harness chỉ gọi actual GenerationMixin config/special-token/length methods qua
PolicyStressBackend và so control không hook. Không gọi model.generate hoặc
Qwen forward. Hai success roles và hai injected error/interruption controls.
Mỗi policy receipt vẫn dùng protocol của **synthetic harness**, nên trường
model_generation_calls=1 trong receipt đó không phải native model inference;
summary bắt buộc ghi model_generate_calls=0 và synthetic-count qualifier.
Không lấy bài kiểm tra này thay native context-stress GPU evidence.

Source files mới: native/stub harness entry, standalone CPU wrapper25-file
additive overlay, exact builder. Local exact package dùng stub, giữ native
progress6workers/layout và8tools/21Dummy/missing-onlyresume trên archive/expanded/
PAX layouts. KernelCPU sau đó mới chạy native thư viện thật và kiểm hashes hai
native implementation source files trước khi gọi. Không local native imports.

Kernel version1 đã COMPLETE, timeout1800s. Source kéo về
`build/kaggle/policy_native_cpu_v1_remote_source01` khớp SHA với exact wrapper;
metadata xác nhận private/offline/CPU/no models/pinned image.
Kaggle pull serialize machine_shape thành string `"None"`; auditor cập nhật
để nhận đúng ba biểu diễn CPU absent (`null`, empty, `"None"`), vẫn từ chối
accelerator/giá trị khác và kiểm enable_gpu/enable_tpu=false riêng.9regression
tests mới,34focused tests đạt; không thay submitted worker/receipts/raw.
Full releaseQA1.743pass/1optional skip375,60s; setup/Ruff/mypy260/knowledge đạt, XML
`results/phase5_policy_native_cpu_v1_release01_pytest.xml`.

Raw `results/phase5_policy_native_cpu_v1_raw01` và remote source nguyên vẹn.
Dummy21tasks/84events đạt; đó là transport, không model quality. Không retry,
không local native models hoặc Testpayload;146frozen source/296oldGPUraw giữ nguyên.
Tiếp: outer publisher-metadata audit + native GPU
stress wrapper. Phase5 vẫn mở; không dùng library success thay inference proof.
