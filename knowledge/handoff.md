# Bàn giao phiên làm việc

Cập nhật: 2026-09-10. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase5 còn mở. IPC diagnostic pair-ipc-v1 đã COMPLETE, một lần submit.
Audits03/04 tái lập selected audit byte-identical,99rawfiles. Nguồn semaphore
observed thuộc tqdm.std.create_mp_lock trong3busy workers;90parent+3idle locks
cóUNREGISTER. Cả6exits vẫn forced (5TERM/1KILL),0graceful.18VRAM samples về nền;
không chứng minh driver/IPC leak-free. [Đính chính](../docs/evaluation/phase5_pair_ipc_gpu_v1_review_addendum.md).

Đang triển khai [pair progress GPU v1](pair_progress_v1.md): entry/wrapper/builder
và auditor riêng đã có. Source `a1a90b3`: 21 test mới đạt, exact preflight cả hai
archive/expanded/PAX layouts đạt, 6 native-policy workers/layout và owner 90/90.
Full pre-submit QA đạt: 1.517 pass/1 optional native skip trong 358,49s;
setup/Ruff/mypy 247 files/knowledge đạt. Chưa GPU submission tại mốc receipt này.
Đã chốt bản sửa opt-in thread-only progress lock và hai native CPU reproductions:
[contract](../docs/architecture/phase5_worker_progress_v1_contract.md),
[tri thức](worker_progress_v1.md). Default/disabled/threadTERM/threadKILL controls
có1/1/0/0registrations; TQDM_DISABLE không phải fix. Chưa sửa frozen GPU/runtime.
Full QA hoàn tất: 1.496 đạt, 1 optional native pytest bỏ qua; XML
`results/phase5_worker_progress_v1_release01_pytest.xml`. Hai standalone native
runs thực sự đã chạy với pinned tqdm, 8 workers/PID khác nhau đều reaped.
Không job Kaggle hoặc model load mới/local weights/Test payload. Full QA mới:
`results/phase5_pair_progress_v1_pre_submit01_pytest.xml` đã hoàn tất.

Có báo cáo tiến độ MD/PDF/figures từ ngoài phiên này;
giữ nguyên, không stage/commit cùng task. Incoming handoff đã giữ nguyên tại
[bản lưu](handoff_20260909_ipc_draft.md); các khẳng định quá rộng được đính chính.

## Bước tiếp theo

1. Versioned GPU lock wrapper/entry với trace/identity; exact archive/expanded/PAX
   8tools/21Dummy/resume, source/receipts push, currentquota/privateinputs rồi mới
   submit một identity mới. Không sửa/retry các kernel cũ để thay kết quả.
2. [Context-stress design](../docs/architecture/phase5_context_stress_v1_design.md):
   chưa implementation/GPU. Exact4096input,512/128output; phân biệt output count
   với actualKVcache. Không benchmarkdecode/promptchange hoặc localmodels.
3. Versioned runtime integration, A4 processing-scope anchors, private-record
   final entitlements, grouped Dev guard/model decision/differential/freeze.
   Không tune từ four-call diagnostic, không Phase6/7/Test access.

Pending access: không tài khoản/model access mới cần cho bước CPU hiện tại.
Kaggle huylmhuhu/kaggle1, systemCLI2.2.4; Dataset11942593private/v1, quota28,89h
chỉ là pre-submit2026-09-09, kiểm lại trước run mới. Không cycling account.
Llama/Meta pilot chưa chạy; không gán điểm0.

## Bằng chứng

- [IPC selected audit](../experiments/manifests/phase5_pair_ipc_gpu_v1_audit01.json):
  source9087791, pre-pushmain31910cb; raw `results/phase5_pair_ipc_gpu_v1_raw01`,
  remote `build/kaggle/pair_ipc_gpu_v1_remote_source01`; audits01–04byte-identical.
  [Pre-submit QA](../experiments/manifests/phase5_pair_ipc_gpu_v1_pre_submit_qa01.json):
  1.481tests/359,83s,51new,setup/Ruff/mypy241files/knowledgepass.
- [Pair cancellation](pair_cancellation_v1.md), [small-context GPU](pair_gpu_v1.md):
  prior62+91raw hashes unchanged. Guard-only olderwarning2alsoimmutable.
- [Worker progress](worker_progress_v1.md): source `e8f72de`, 15 unit mới đạt;
  full suite 1.496 đạt/1 skip trong 354,52s, setup/Ruff/mypy 243 files/knowledge đạt.
  [Selected receipt](../experiments/manifests/phase5_worker_progress_v1_validation01.json)
  và [release QA](../experiments/manifests/phase5_worker_progress_v1_release_qa01.json)
  bind hai native runs bằng system Python 3.11.0/tqdm 4.67.3; mỗi lượt 7 raw files,
  registrations 1/1/0/0, warning 2 positive controls. Không dùng prototype dev01
  làm selected release. Frozen sources/overlays/raw GPU và seals hash-only đạt.
- [Gate còn lại](phase5_progress.md), [README](README.md) dẫn tới các mốc CPU/GPU
  và các phase đã accepted. Không merge nhánh bạn:
  [review](phase5_integration_review_20260909.md).

## Giới hạn

Worker reap, graceful exit, VRAM recovery và IPC cleanup là các kết luận khác nhau.
IPC trace không quan sát cachedaliases/Cregistrations/trackerOSunlink; timings
instrumented không gộp với lượt trước. Thread-only lock chưa GPU/HF verified.

Không privateGT/Testpayload/credentials/hiddenreasoning trong memory; memory không
đi vào prompts. Test seals chỉ hash-check, không model Test. Phase1–4 đã accepted
theo scope/owner self-review waiver; Phase5 chưa accepted. Không lấy số tests pass
làm phần trăm hoàn thiện hoặc bằng chứng chất lượng/security LLM.
