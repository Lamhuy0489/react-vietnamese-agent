# Seven-level native runtime package v1

2026-09-13. CPU02/preflight03 đạt; GPU version 1 COMPLETE, independent audit đạt.

## Kết quả hiện hành

205 raw/2 remote files khớp; local joined audits bằng byte với remote receipt.
7/7 terminal completed và VRAM recovered, nhưng **0 tool calls, 0 guard calls**:
model trả lời thẳng 391. Không phải 7/7 utility hoặc kiểm chứng guard protection.
12 workers TERMINATE/-15, chưa graceful. Không retry kết quả semantic này.
[GPU report](../docs/evaluation/phase5_security_runtime_gpu_v1_report.md) và
[receipt](../experiments/manifests/phase5_security_runtime_gpu_v1_audit01.json).
Release auditor full QA: 2.596 pass/1 skip, 566,82s; 13 tests mới,
setup/Ruff/mypy 328 files/knowledge đạt. 458 source/2.859 raw hashes khớp,
169 data hashes không đổi. Không còn job CPU/GPU đang chạy ở mốc này.

Tiếp: graceful worker lifecycle bằng version mới/CPU acknowledgement negatives,
sau đó native diagnostic mới có mục tiêu coverage được định trước. Giữ nguyên
source/runtime/prompt/output của calculator pilot; không sửa để lấy điểm cao hơn.

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
`notebooks/kaggle/security_runtime_kernel_v1.py`: 82 overlay files, kế thừa base
bundle03 và giữ source cũ. Exact archive/expanded isolated mount đã đạt:
8 tools/fault recovery, 21 public Dummy/resume, ordinary diagnostics và
7-level new stub runtime/resume. Native metrics parent phải tạo sau fresh-root
validation, trước worker start (đã có regression test).

Full QA CPU02: **2.583 pass/1 native-tqdm skip**, pytest 550,20s;
23 focused tests, setup/Ruff/mypy 327 files/knowledge đạt.
Source `372d68588eab3fbdeabf7464a9173cbdac9b6ba0`; 456 source/2.859 raw hashes
được kiểm độc lập, 169 data hashes không đổi. 8 real-spawn synthetic receipts;
42 mocked native-shaped fixture records không phải native inference.
[CPU02 receipt](../experiments/manifests/phase5_security_runtime_probe_v1_cpu02.json)
SHA-256 `f255b93ab023013b2cf7c4ba21ff134fe3804034347e0aed1da139715855e336`.
[Preflight03 receipt](../experiments/manifests/phase5_security_runtime_v1_preflight03.json)
SHA-256 `fc3e43ff648263cbceea5d7e30590edb7061dac11c8aab6fc5baa30ba8fb75f7`:
88 selected source files, 82 overlay files, 426 raw files; mỗi mount 7/7 levels
completed/recovered, missing-only resume giữ checkpoint. Không load model local.
CPU01 source thay đổi trong lúc QA nên không chọn, raw giữ nguyên.

Kaggle read-only pre-upload: owner `huylmhuhu`, Dataset
`react-vn-guard15-probe-data-v1` private/ready/current version 1; tên kernel
`react-vn-security-runtime-v1` chưa tồn tại khi kiểm. Quota snapshot 29,86h GPU
còn lại, không phải reservation. Upload chỉ sau source/evidence push.

Sau khi push `d1e3e27`, đã submit kernel **version 1**, timeout 7200s,
`NvidiaTeslaT4`; status đầu tiên RUNNING. Không có lần GPU retry.
CLI pull với `/1` trả 403 trong khi status tên hiện hành đọc được; dùng tên
hiện hành để kiểm hash source (chưa tạo version 2). Đây là lỗi đọc metadata,
không phải lỗi model hoặc lý do submit lại.

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
