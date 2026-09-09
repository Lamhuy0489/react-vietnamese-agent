# IPC-origin diagnostic — đang chuẩn bị

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

Tiếp: full QA, commit source, exact archive/expanded/PAX preflight, push receipts,
verify quota/private Dataset và submit một private twoT4 identity pair-ipc-v1.
Không job/model/GPU mới đang chạy; chưa có live attribution. Không cần account
mới hoặc Test/private GT. Sau audit mới cân nhắc lifecycle fix/version phù hợp;
context stress/runtime/Dev/A4/final vẫn là các gate còn lại của Phase5.
