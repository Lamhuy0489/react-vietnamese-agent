# Attention cho request thường — bước nền CPU

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
Full QA đang chạy: `results/phase5_efficient_requests_v1_cpu01_pytest.xml`.
Không GPU mới, local models hoặc Test/privateGT. Chưa thay phase acceptance.

Tiếp: independent request receipt auditor + join native metrics; real-spawn
factory/Ready/progress composition và repeated-request GPU proof trước adoption.
Runtime v5 tự tạo WarmGuardBackend, không được nhét ModelPair vào factory để
spawn lồng nhau. ModelPair.start hiện load cả hai roles; A0/A1 phải agent-only,
không được load guard. Cần versioned task owner và worker routing, cold/warm/task
accounting và A0–A6 differential tests riêng; không sửa frozen v5/ModelPair.

Giữ nguyên các file plan6–9 rỗng và báo cáo ngoài nhiệm vụ, không commit cùng.
