# Bàn giao phiên làm việc

Cập nhật: 2026-09-09. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Hiện hành: theo owner clarification, model lớn chỉ ở Kaggle. Triển khai read-only
agent mount authenticator;29targetedtests pass, fullsuite đang chạy. Chưa submit.
[Contract](../docs/architecture/phase5_agent_mount_v1_contract.md),
[tri thức](agent_mount_v1.md). Không tải Qwen7B về local hoặc cần mở rộng disk.
Next: commit/render/preflight/push rồi một CPU/offline Kaggle hash-only job.

Mốc hiện hành: CPU-only placement admission đã triển khai;56targetedtests pass,
full QA1.143tests/241,49s pass. [Contract](../docs/architecture/phase5_coexistence_placement_v1_contract.md),
[bằng chứng/giới hạn](coexistence_placement_v1.md).
Qwen7B candidate chia20/8layers, agent process caps12/7GiB và guard5GiB/device1;
globalheadroom1GiB/device riêng. Không model selection hoặc combined-fit claim.
Chưa agent snapshot authenticated/budgeted HF loader hoặc GPU submission mới.
Source2f311bb đã tái lập hai lần, receipts validation01/02 byte-identical.
[Selected CPU receipt](../experiments/manifests/phase5_placement_v1_validation01.json).
Upstream Qwen7B14files/fourshards được xác minh ở revision cố định; config663bytes
khớp Git blob và geometry. Không tải weights. Disk17,36GiB còn: không đủ
workflow nhiều bản copy của snapshot14,20GiB; xem phương án pinned Kaggle mount
và publisher-hash verification hoặc cần storage lớn hơn, không tự xóa artifacts.

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

1. CPU placement QA/receipt đã hoàn tất; tiếp theo xác thực read-only Kaggle agent mount
   và separate budget-enforcing HF adapter. Không dùng nguyên
   MeasuredHFBackend13GiB/device. Sau CPU fake/context tests và exact packaging,
   predeclare combined residency/context stress trước GPU; frozen source giữ nguyên.
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
