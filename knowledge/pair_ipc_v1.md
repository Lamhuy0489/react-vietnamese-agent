# IPC-origin diagnostic — exact preflight và QA đã pass

Mốc trước: [pair cancellation](pair_cancellation_v1.md) GPU pass resource gates,
warning3semaphores chưa xác định nguồn. Không sửa hoặc thay thế kết quả cũ.

[Contract](../docs/architecture/phase5_pair_ipc_v1_contract.md): diagnostic mới giữ
13overlay cũ, thêm tracer/entry point; không manual unregister/unlink, không đổi
grace, không model.generate. Trace chỉ PID/role/hash tên resource/metadata stack,
không locals/source text/prompt/credentials. Owner GC checkpoint được khai báo
riêng, không coi là sửa cleanup; tracker/OS unlink chưa được quan sát trực tiếp.

CPU prototype source chưa commit: `results/phase5_pair_ipc_cpu_dev01`, ba ca pass;
parent90register/90unregister,6stub workers zero registrations. Đây là development
check trước final source, không selected release hoặc bằng chứng GPU. Positive
control test giết một process tự sở hữu semaphore để xác minh unmatched/warning.

Source9087791 exact preflight đã pass archive/expanded/PAX,8tools/21Dummy/
missing-only resume/three stub trials,90parent REGISTER/90UNREGISTER mỗi layout.
[Receipt](../experiments/manifests/phase5_pair_ipc_gpu_v1_preflight01.json).
Full finalQA1.481tests/359,83s pass,51new (31tracer/wrapper+20audit);
setup/Ruff/mypy241files/knowledge pass.
[QA](../experiments/manifests/phase5_pair_ipc_gpu_v1_pre_submit_qa01.json).
Ngày2026-09-09 quota28,89h, Dataset11942593 private/version1/ready verified;
không phải quota reservation. Tiếp: push receipts rồi submit một private twoT4
identity pair-ipc-v1. Audit implementation đã có, chưa actual GPU attribution.
Không job/model/GPU mới đang chạy; chưa có live attribution. Không cần account
mới hoặc Test/private GT. Sau audit mới cân nhắc lifecycle fix/version phù hợp;
context stress/runtime/Dev/A4/final vẫn là các gate còn lại của Phase5.
