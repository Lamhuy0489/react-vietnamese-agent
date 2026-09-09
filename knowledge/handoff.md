# Bàn giao phiên làm việc

Cập nhật: 2026-09-09. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Hiện hành: combined small-context pair GPU đã COMPLETE và kiểm tra lần submit1.
Kernel `huylmhuhu/react-vn-pair-gpu-v1` private/offline/twoT4/version1;
sourceb76c040/preflight push main6596802 trước GPU. Dataset11942593 private/v1.
[Report](../docs/evaluation/phase5_pair_gpu_v1_report.md),
[review receipt](../experiments/manifests/phase5_pair_gpu_v1_review01.json),
[tri thức](pair_gpu_v1.md). Agent/guard cold264,423/33,033s,warm1,906/1,788s.
Resident delta9,799/7,621GiB, six recovery samples residual0bytes haiGPU.
Hai workers TERMINATE/-15/reaped; không graceful. Không quality/max-context claim.
62raw files `results/phase5_pair_gpu_v1_raw01`; remote source02 hashmatch.
Hai inspections01/02 byte-identical;21Dummy/84events checked,146frozen entries
nguyên vẹn. Full release1.363tests/339,69s pass,11new inspector tests; XML
`results/phase5_pair_gpu_v1_release01_pytest.xml`. Setup/Ruff/mypy230files/knowledge pass.
[Release QA](../experiments/manifests/phase5_pair_gpu_v1_release_qa01.json).
Không test/Kaggle/model job đang chạy; không retry. Không localweights/Test payload.
Không pending access mới. Bước tiếp: freeze protocol max-context và
combined cancellation trước GPU, rồi pair integration vào version mới của runtime,
grouped Dev guard/model decision và phạm vi A4/final còn lại. Phase5 chưa accepted.

Mốc lịch sử: ModelPair supervisor và durable residency probe đã triển khai riêng;
56newtests pass (37supervisor/19probe), setup/Ruff/mypy224files pass. Full final
suite1.330tests/326,86s pass, XML `results/phase5_model_pair_v1_final01_pytest.xml`.
[Contract](../docs/architecture/phase5_model_pair_v1_contract.md), [tri thức](model_pair_v1.md).
First preflight chỉ là lịch sử trước script line wrapping. Hai clean-source
rehearsals6d1c761 validation01/02 có2syntheticcalls/run, reaped/giả lập recovery;
stable summaries/source hashes khớp,15raw files/run giữ PID/timing riêng. Cả4CPU
workers GRACEFUL; không thay kết quả GPU cũ. [Receipt](../experiments/manifests/phase5_model_pair_v1_validation01.json),
[report](../docs/evaluation/phase5_model_pair_v1_report.md). Không còn test process.
Tiếp theo HF entry point và exact worker overlay/mount preflight trước GPU. Không
model/GPU/Kaggle submission mới hoặc local weights; Test chỉ hash-check.

Mốc lịch sử: runtime-input admission và agent HF loader12/7GiB đã triển khai riêng;
87new CPU fake tests pass, Ruff/setup/mypy221files pass. Full final-source QA
1.274tests/278,23s pass; JUnit lưu trong results. Không chọn run1269tests trước
thay đổi native config defaults hoặc final01 mất process handle làm QA cuối.
Hai clean-source reproductionsfa894c4 byte-identical; không còn test process.
[Selected receipt](../experiments/manifests/phase5_agent_loader_v1_validation01.json),
[report](../docs/evaluation/phase5_agent_loader_v1_report.md).
[Contract](../docs/architecture/phase5_agent_hf_v1_contract.md),
[tri thức](agent_loader_v1.md). Chưa live header/model load/combined GPU hoặc
submission mới. QA/source/reproduction đã xong; tiếp theo supervised combined
GPU protocol và exact bundle preflight. Không cần GPU/download weights local.

Mốc lịch sử: theo owner clarification, model lớn chỉ ở Kaggle. Triển khai read-only
agent mount authenticator;29targetedtests pass, fullsuite1.172tests/263,13s pass.
Setup/Ruff/mypy216files/knowledge pass. CPU diagnostic submitv1 thành công;
actual handle `huylmhuhu/react-vn-agent-mount-auth-v1` do title/slug mapping.
Không submit lại; giữ requested metadata, kiểm sourcehash theo actual handle.
CPU job đã kết thúcERROR do full-inventory mismatch đúng dự kiến. 11/11runtime
files match, chỉ README khác. [Report](../docs/evaluation/phase5_agent_mount_v1_report.md),
[scan](../experiments/manifests/phase5_agent_mount_v1_scan01.json),
[audit](../experiments/manifests/phase5_agent_mount_v1_audit01.json).
Raw `results/phase5_agent_mount_v1_raw01` có2files(log/receipt); remote source
`build/kaggle/agent_mount_remote_source01`, audit01/02 tái tạo byte-identical.
15audit tests pass, fullsuite1.187tests/238,38s pass;setup/Ruff/mypy218files/
knowledge pass. Không job đang chạy. Tiếp theo versioned runtime-input
admission cho matching runtime bytes + known README difference, rồi budgeted
agent HF loader. Chưa combined GPU run; không cần GPU/disk/model download local.
[Contract](../docs/architecture/phase5_agent_mount_v1_contract.md),
[tri thức](agent_mount_v1.md). Không tải Qwen7B về local hoặc cần mở rộng disk.
CPU source/preflight đã push2db4496 trước first submission; không submit thêm.

Mốc lịch sử: CPU-only placement admission đã triển khai;56targetedtests pass,
full QA1.143tests/241,49s pass. [Contract](../docs/architecture/phase5_coexistence_placement_v1_contract.md),
[bằng chứng/giới hạn](coexistence_placement_v1.md).
Qwen7B candidate chia20/8layers, agent process caps12/7GiB và guard5GiB/device1;
globalheadroom1GiB/device riêng. Không model selection hoặc combined-fit claim.
Tại mốc placement chưa xác thực agent snapshot; CPU diagnostic phía trên đã
kiểm runtime hashes. Budgeted HF loader và combined GPU vẫn chưa triển khai.
Source2f311bb đã tái lập hai lần, receipts validation01/02 byte-identical.
[Selected CPU receipt](../experiments/manifests/phase5_placement_v1_validation01.json).
Upstream Qwen7B14files/fourshards được xác minh ở revision cố định; config663bytes
khớp Git blob và geometry. Phương án nhiều bản copy local đã được thay bằng
pinned Kaggle mount theo owner; không yêu cầu thêm storage hoặc xóa artifacts.

Phase5: cancellation/GPU-memory-recovery v1 đã hoàn tất và audit. Owner yêu cầu
tiếp tục trên main, chỉ lấy nhánh bạn nếu cần. Không cherry-pick/merge
phase5-integration: A0/A1 QA đã có, các sửa khác chưa đạt.
[Review nhánh](phase5_integration_review_20260909.md) giữ nguyên, không sửa nhánh bạn.

Kernel `huylmhuhu/react-vn-guard-cancel-run-v1` version1 COMPLETE lần submit đầu.
Source/receipt push main52004ea trước GPU; runtime7649d5b, overlay/bootstrapdab6c64.
Dataset v1 riêng tư giữ nguyên, kernel private/offline/twoT4, worker device1.
[Báo cáo](../docs/evaluation/phase5_guard_cancellation_v1_report.md),
[audit](../experiments/manifests/phase5_guard_cancellation_v1_audit01.json),
[contract](../docs/architecture/phase5_guard_cancellation_v1_contract.md).

Ba fresh workers tải Qwen1.5B pinned snapshot, không model.generate.
ACK gồm load43,995/30,628/30,177s; busy deadlines120,335/120,822s.
Resident3,047GiB mỗi ca; cả18samples sau reap residual0MiB.
Hai TERMINATE/-15, ignore-term KILL/-9. Normal close vẫn không graceful.
Mốc resource recovery đạt contract; Phase5 chưa accepted.

## Bước tiếp theo

1. HF entry point và adapter v2 đã có; chốt full QA/source và exact builder
   archive/expanded packaging/eight tools/21Dummy/resume
   trước GPU. Không dùng MeasuredHFBackend13GiB/device hoặc coi allocator cap là
   proof of fit. Frozen source giữ nguyên; large models chỉ chạy trên Kaggle.
2. Grouped Dev protocol/model decision rồi A4 scope/general final entitlements.
   First guard GPU B vẫn SAFE, bốn A/B outputs giống nhau; không chốt Qwen1.5B
   làm guard production hoặc tune từ four-call diagnostic.
3. Giữ graceful-close failure tách resource recovery; nếu điều tra/sửa lifecycle
   phải có version/protocol mới, không đổi grace để biến số đo cũ thành pass.
4. Không Phase6/7, không Test inference/GT hoặc semantic retries.
5. Account huylmhuhu (kaggle1), CLI python3 -m kaggle2.2.4. Pre-submit ngày
   2026-09-09 còn29,45h, không phải quota hiện tại/giữ chỗ; kiểm lại trước run mới.
   Không cần tài khoản mới hoặc pending model-access cho mốc vừa xong.
   Không job test/kernel/upload đang chạy sau completion; không submit lần hai.

## Bằng chứng

- [Model pair release QA](../experiments/manifests/phase5_model_pair_v1_release_qa01.json):
  source6d1c761,1.330tests/326,86s;56newtests. Hai clean-source rehearsals giữ
  30raw files +2receipts, stable summaries equal, raw PID/timing hashes khác nhau.
  140prior source entries nguyên vẹn; model/memory giả lập, zero GPU/Test payload.
- [Agent loader QA](../experiments/manifests/phase5_agent_loader_v1_release_qa01.json):
  sourcefa894c4,1.274tests/278,23s với JUnit durable,87newtests; setup/Ruff/
  mypy221files/knowledge pass. Hai clean-source CPU reproductions byte-identical,
  134frozen hashes và Test seals nguyên vẹn. Không GPU/model load hoặc live header.
- [Agent mount release QA](../experiments/manifests/phase5_agent_mount_v1_release_qa01.json):
  1.187 tests/238,38s, 44 scanner/audit tests mới; setup/Ruff/mypy218files/knowledge
  pass. Hai audit byte-identical, 134 frozen source hashes giữ nguyên; không
  model load/GPU/local agent weights. Full inventory vẫn bị từ chối vì README.
- Final placement suite1.143tests/241,49s;56newtests. Setup/Ruff/mypy215files
  gồm cancellation wrapper và knowledge pass. Basetemp
  `build/pytest_placement_v1_final01`. Không test/model/kernel job đang chạy.
  Selected receipt byte-identical từ source2f311bb sạch;134frozen sources và
  67prior cancellation raw hashes giữ nguyên. Không Phase5 acceptance mới.
  [Placement QA receipt](../experiments/manifests/phase5_placement_v1_release_qa01.json).
- Full1.087tests/257s, basetemp `build/pytest_guard_cancel_audit_v1_01`;
  20 tests mới cho read-only cancellation audit. Setup/Ruff/mypy213files gồm
  cancellation wrapper pass. Lần trước1.067tests/256,77s cũng pass trước GPU.
  [Release QA receipt](../experiments/manifests/phase5_guard_cancellation_v1_release_qa01.json).
- [Exact preflight](../experiments/manifests/phase5_guard_cancellation_v1_preflight01.json)
  hai isolated archive/expanded PAX mounts: eight tools/fault,21Dummy/resume,
  complete cancellation CPU-stub protocol. Selected receipt byte-identical.
- Raw `results/phase5_guard_cancellation_v1_raw01`:67files, đầy đủ log/Dummy/probe.
  Audit01 và audit02 dưới results tái tạo JSON/report byte-identical.
  Remote `build/kaggle/guard_cancellation_remote_source01`: source/metadata
  tải ngược, wrapper khớp preflight; metadata private/offline/T4.
- 21Dummy/84trace events/checkpoint identity được audit; 67raw/134prior adapter
  source hashes kiểm lại; credential scan71files/0matches. Test seal hash-only.
- Dataset `huylmhuhu/react-vn-guard15-probe-data-v1` READY/v1/private trước run.
  Bundle03 và weights `build/guard_models/qwen1_5b_hf_v1_acquisition01` giữ nguyên.
- [First guard GPU report](../docs/evaluation/phase5_guard_gpu_v1_report.md),
  [QA](../experiments/manifests/phase5_guard_gpu_v1_release_qa01.json) giữ nguyên;
  raw56files và auditv1 cleanup rejection không bị thay thế.

## Giới hạn

Parent CUDA observer có context ổn định suốt probe, khác run cũ không có parent
CUDA. Sáu samples1s/last3±256MiB là contract; không timestamp từng sample,
không global peak hoặc chứng minh zero leak mọi tải. Không agent resident,
không combined/context stress hoặc benchmark quality. Model generation0.
Project memory không đi vào model prompts; không private GT/Test payload/CoT.
Assistant self-review theo owner waiver, không independent human review.
