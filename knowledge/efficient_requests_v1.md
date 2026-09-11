# Attention cho request thường — bước nền CPU

## Cập nhật mới: auditor request/native metrics

Đã thêm `validation/efficient_requests_audit_v1.py` và CLI
`scripts/audit_phase5_efficient_requests.py`, giữ nguyên adapter source039af85.
[Contract auditor](../docs/architecture/phase5_efficient_requests_audit_v1_contract.md).
78 test mới và 46 test adapter đạt (124 tổng, 23,79s), gồm actual sidecar writer
với fake tensors/native metrics, request ngắn/dài/A-B-A, corruption, readonly,
CLI không ghi đè. Không phải bằng chứng native model execution.
Full QA hoàn tất: 2.055 pass, 1 optional skip (native tqdm thiếu), không lỗi;
JUnit suite time454,190s, `results/phase5_efficient_requests_audit_v1_cpu01_pytest.xml`.
Source `35fdad8`; [QA receipt](../experiments/manifests/phase5_efficient_requests_audit_v1_cpu_qa01.json).
Setup/Ruff/mypy285/knowledge đạt; 106 frozen overlay entries, 277 historical raw
files và prerequisite seals không đổi. Không test job còn chạy tại bàn giao.

Auditor đối chiếu input/output token với geometry, thứ tự/PID/model/config,
restore flags, thời gian load/generate/call; không chọn bỏ lỗi hoặc request thiếu.
PID là kỳ vọng do caller đưa, chưa xác thực supervisor; native load memory,
resolved publisher policy và full-boundary KV chưa được chứng minh bởi auditor.
Không copy unknown native metadata vào report. Không GPU/Test/privateGT mới.

Đã thêm [real-spawn composition CPU](request_pair_v1.md) với ReadyFactory ngoài cùng, thread-only progress
trước load, metrics/attention roots riêng và request index không tính readiness.
Sau đó versioned repeated-request native GPU preflight/proof; task owner/runtime
routing và A0–A6 differential còn mở. Không cần quyền/tài khoản mới cho mốc CPU.

## Lịch sử: adapter CPU đã kiểm

Owner yêu cầu tiếp tục sau efficient stress pass. Đã thêm module riêng
`src/react_agent/llm/efficient_requests_v1.py`, không sửa source đã freeze.
[Contract và ràng buộc tích hợp](../docs/architecture/phase5_efficient_requests_v1_contract.md).

Adapter giữ nguyên native generate/config/prompt; nhận input1–4096 và số forward
thay đổi theo request, không forced output/extra final forward/profiler. Nhiều
request thành công dùng chung worker trong một task; reset geometry mỗi lần,
restore HF/Torch bindings và flags, retire vĩnh viễn sau lỗi. Supervisor/runtime
vẫn phải đảm nhận task ownership và cleanup; chưa được nối vào vòng ReAct.

46 focused tests đạt0,91s, gồm pinned HF source với fakeTensor/mask/no-mask và
variable requests; không native GPU numerical/cache-statelessness claim.
Full QA: 1.977 pass, 1 optional skip (native tqdm thiếu), 437,99s;
setup/Ruff/mypy283/knowledge đạt. Source `039af85`;
[CPU QA receipt](../experiments/manifests/phase5_efficient_requests_v1_cpu_qa01.json)
ghi hash source và JUnit local `results/phase5_efficient_requests_v1_cpu01_pytest.xml`.
Đã kiểm lại 106 frozen overlay entries, 277 historical raw files và prerequisite
seals không đổi. Không cần quyền truy cập mới để hoàn tất mốc CPU này.
Không GPU mới, local models hoặc Test/privateGT. Chưa thay phase acceptance.

Auditor/native metric join đã thêm ở cập nhật trên; real-spawn
factory/Ready/progress composition và repeated-request GPU proof vẫn còn trước adoption.
Runtime v5 tự tạo WarmGuardBackend, không được nhét ModelPair vào factory để
spawn lồng nhau. ModelPair.start hiện load cả hai roles; A0/A1 phải agent-only,
không được load guard. Cần versioned task owner và worker routing, cold/warm/task
accounting và A0–A6 differential tests riêng; không sửa frozen v5/ModelPair.

Giữ nguyên các file plan6–9 rỗng và báo cáo ngoài nhiệm vụ, không commit cùng.
