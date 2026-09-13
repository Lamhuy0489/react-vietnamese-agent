# Seven-level native runtime package v1

2026-09-13. Đang triển khai; 22 focused tests pass/15,02s, chưa có GPU run mới.

## Nguồn mới

`native_agent_only_v1` ghép đúng cùng ThreadProgress/RequestPolicy/EfficientRequest/
AgentFactoryV2 như paired agent, không tạo guard. `security_runtime_probe_v1`
chạy public calculator task qua runtime v2/v7, A0–A6, một state và worker set/task.
Checkpoint hash toàn bộ raw, resume chỉ task chưa chạy, giữ semantic/model errors,
refuse partial/unrecovered output. Sáu memory samples sau cleanup/task.

Native joined auditor kiểm model admission/publisher/tokenizer, worker PID,
policy/attention, token/timing. Failed role giữ partial/unassessed; zero guard
calls không chứng minh guard operational. Synthetic native-shaped tests mock
checkpoint boundary được gắn rõ, không tính như native execution.

## Package và xác minh cần hoàn tất

Builder `scripts/prepare_phase5_security_runtime.py`, wrapper
`notebooks/kaggle/security_runtime_kernel_v1.py`: 83 overlay files, kế thừa base
bundle03 và giữ source cũ. Exact archive/expanded isolated mount cần chạy trước
upload: 8 tools/fault recovery, 21 public Dummy/resume, ordinary diagnostics và
7-level new stub runtime/resume. Native metrics parent phải tạo sau fresh-root
validation, trước worker start (đã có regression test).

Full QA runner `scripts/verify_phase5_security_runtime_probe.py` dự kiến output
`results/phase5_security_runtime_probe_v1_cpu01`. Không gọi accepted trước receipt.

## Giới hạn

Agent-only có deadline startup/call chung 1200s, paired 1200s startup/180s call;
pilot ghi rõ khác biệt, không claim lợi thế timing/timeout xuyên levels. Cùng
agent/model/decoding/prompt/tools/attention. Đây là technical pilot, không final
security benchmark. Không đọc Test/privateGT hoặc đổi policy theo Test.
Phase 5 còn GPU lifecycle, production guard/grouped Dev, broader coverage/freeze.

## Preflight01 deviation

Exact archive mount bắt được `ModuleNotFoundError: validation.clean_pool` từ
repository validation initializer. Không thêm benchmark QA vào worker để chữa lỗi;
bỏ initializer khỏi overlay, giữ namespace package như ordinary bundle cũ.
Overlay mới 82 files. Giữ build/preflight01 và QA CPU01 làm development history;
source thay đổi nên CPU01 không chọn làm acceptance. Chạy preflight02 và QA CPU02
từ commit mới. Chưa GPU submission, không phải model/semantic retry.

Preflight02 chạy xong base import/8 tools/21 Dummy/resume/ordinary audits, rồi
phát hiện runner còn import `schemas.adversarial_workbench`. Thay bằng schema
public hai trường ngay trong probe, không đưa authoring schema vào worker.
Giữ preflight02; tiếp preflight03 sau source commit mới. Chưa gửi GPU.

[Contract](../docs/architecture/phase5_security_runtime_probe_contract.md) ·
[Handoff](handoff.md).
