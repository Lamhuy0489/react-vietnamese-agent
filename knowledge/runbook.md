# Runbook hiện hành

Chạy tại root repo. Dùng `.venv/bin/python`; không coi lệnh từ ghi chú v1
lịch sử là lệnh hiện hành. Đọc [bàn giao](handoff.md) trước khi chạy inference.

## Kiểm tra phần mềm và bộ nhớ

Phase 5 value PreGate/Post-view QA hiện hành (output/report luôn mới):

```bash
.venv/bin/python scripts/verify_phase5_value_gates.py \
  --reference experiments/manifests/phase5_value_gates_v1_validation02.json \
  --output results/phase5_value_gates_next_check \
  --report results/phase5_value_gates_next_check.json
```

24 Pre/sáu Post component cases, bốn mock Broker calls. 769 tests; không model/
guard/Replay inference, Test hash-only. Source/test/contract đã hash giữ bất biến;
Selected validation02 từ source sạch `a3743a2` khớp preflight02, 769 tests pass;
132 source/121 raw hashes đã kiểm lại. Selected mới cần source sạch và reference
cùng source hashes. Dùng output/report mới; không ghi đè lượt đã có.
Preflight01 bị source-changed trong review, không dùng làm evidence đã chọn.
Validation01 gián đoạn trước receipt; giữ nguyên, validation02 chạy mới toàn bộ QA.

Phase 5 value-origin/final-release QA lịch sử (output/report luôn mới):

```bash
.venv/bin/python scripts/verify_phase5_value_origin.py \
  --reference experiments/manifests/phase5_value_origin_v1_validation01.json \
  --output results/phase5_value_origin_next_check \
  --report results/phase5_value_origin_next_check.json
```

24 synthetic conditions: 12 ALLOW/8 REDACT/4 DENY; không Replay/model/guard run.
Suite 696 tests, setup/Ruff/mypy 183 files/knowledge pass. Source `3b9f565`,
selected receipt khớp preflight; 130 source/101 raw hashes kiểm lại. Test hash-only.
Component chưa bật A6 runtime. Source/test/contract đã hash không sửa tại chỗ;
thêm version riêng khi tích hợp Pre/Post/Final hoặc mở rộng matching profile.

Phase 5 session QA lịch sử (output/report luôn mới):

```bash
.venv/bin/python scripts/verify_phase5_session.py \
  --reference experiments/manifests/phase5_session_v1_validation01.json \
  --output results/phase5_session_next_check \
  --report results/phase5_session_next_check.json
```

44 A0–A2 parity pairs + 30 synthetic A3–A5 conditions = 118 Replay. Session cases
có 165 fake guard classifications, 225 snapshots. Suite 593 tests, Test hash-only.
Không guard model thật, không ASR/throughput claim. Chạy selected từ source sạch
với `--reference` trỏ preflight cùng source hashes. A6 vẫn chưa được hỗ trợ.
Source milestone `8a4ca3d`; selected receipt khớp preflight/source/raw hashes.

Phase 5 A2 QA lịch sử (output/report luôn mới):

```bash
.venv/bin/python scripts/verify_phase5_a2.py \
  --reference experiments/manifests/phase5_a2_v2_validation01.json \
  --output results/phase5_a2_next_check \
  --report results/phase5_a2_next_check.json
```

40 A0/A1 smoke pairs + chín A2 synthetic cases = 89 Replay, 31 fake guard calls.
Suite 446 tests; Test hash-only, không guard model thật. Worker cold-start mỗi cache
miss, deadline gồm load/generate; không dùng số này làm GPU throughput.
Selected report cần source sạch + `--reference` trỏ preflight cùng source hashes.
Source milestone `15ed921`; receipt hiện hành đã khớp preflight/source/raw hashes.

Phase 5 runtime v1 lịch sử (source đã hash, output/report luôn mới):

```bash
.venv/bin/python scripts/verify_phase5_runtime.py \
  --reference experiments/manifests/phase5_runtime_v1_validation01.json \
  --output results/phase5_runtime_next_check \
  --report results/phase5_runtime_next_check.json
```

20 smoke A0 pairs + 24 synthetic differential conditions = 64 Replay, cùng quality
checks (suite hiện 366 tests). No benchmark Dev/model run, Test hash-only. Source
khác receipt sẽ bị từ chối: khi triển khai tiếp cần version/phạm vi QA mới; không
ghi đè evidence. [Contract](../docs/architecture/phase5_runtime_contract.md).

Phase 5 component QA (synthetic micro-tests, chưa benchmark/model evaluation):

```bash
.venv/bin/python scripts/verify_phase5_components.py \
  --output results/phase5_components_next_check \
  --report results/phase5_components_next_check.json
```

Source/report paths mới; 56 micro-tests, hash-only Test, không model inference.
Suite toàn repo hiện 300 tests. [Tiến độ và giới hạn](phase5_progress.md).

Phase 4 đã nghiệm thu, suite hiện 244 tests. Tái lập closure CPU khi cần (tất cả
đường dẫn output/report phải mới, không ghi đè selected receipt):

```bash
.venv/bin/python scripts/verify_phase4_closure.py --quality \
  --reference experiments/manifests/phase4_closure_v1_validation01.json \
  --output results/phase4_closure_next_check \
  --report results/phase4_closure_next_check.json
```

45 Dev pairs/90 Replay + 440 smoke overhead + hai stress. Không inference LLM;
Test hash-only. Cần giữ local raw evidence của runtime receipt cũ để audit các
hash trước đó; fresh clone thiếu raw không được giả là đã audit. Source/reference
hashes phải khớp; thay đổi source sau freeze cần version/phạm vi validation mới.
`--qa-only` bỏ đo overhead, không đủ để tự cấp nghiệm thu. [Báo cáo](../docs/architecture/phase4_report.md).

Phase 4 runtime parity (output/report phải mới):

```bash
.venv/bin/python scripts/verify_phase4_runtime.py \
  --output results/phase4_runtime_next_check \
  --report results/phase4_runtime_next_check.json
```

65 paired conditions/130 Replay, không LLM/Test inference. Suite có đọc reference
actions/faults của clean Dev trong QA; không đưa oracle vào runtime/catalog/prompt.
Adversarial Dev chỉ public trigger probes, không đọc private authoring pools hoặc
archive Test. Không gọi `load_selected` cho công việc mới. Suite hiện 224 tests;
các số 185/132 bên dưới là mốc lịch sử. [Tiến độ](phase4_progress.md).

Phase 4 primitive QA (report phải mới, chỉ đọc nội dung Dev):

```bash
.venv/bin/python scripts/verify_phase4_primitives.py \
  --report results/phase4_primitives_next_check.json
```

1.650 kiểm tra ba profile trên 550 Dev texts; kiểm tra hash Test/50 robustness
IDs, không đọc Test payload hoặc GT trong validator này. Không chạy model/tools.
Sau mốc Phase 4 đầu, suite hiện có 185 tests; con số 132 bên dưới là mốc Phase 3.

Phase 3 đã seal: không dùng các lệnh authoring/Replay lịch sử bên dưới cho
phát triển phase tiếp theo. Chỉ chạy kiểm tra hash và nạp Dev:

```bash
.venv/bin/python scripts/assemble_adversarial_release.py --action check
```

`react_agent.adversarial_release.load_split(release)` mặc định Dev (400 records),
không mở Test. Chỉ đưa `fixture.task` vào Runtime; overlay/resources dùng để dựng
tools. Không đưa cả fixture vào prompt. Test cần phạm vi đánh giá được cho phép.
`pytest` sau seal không collect 650 construction tests cũ trước import; 132 tests
còn lại gồm seal integrity/Dev-only loading. Lượt full trước seal đạt 782 tests.
Không gỡ seal để chạy lại authoring tests. [Nghiệm thu](../docs/benchmark/adversarial_release_v2_summary.md).

```bash
.venv/bin/python scripts/verify_setup.py
.venv/bin/ruff check .
.venv/bin/mypy src scripts
.venv/bin/pytest
make knowledge-check
```

Các lệnh này không gọi LLM. Một số test đọc split để kiểm tra tính toàn vẹn;
đó không phải held-out model evaluation. `make check` còn dựng smoke environment
Phase 1; dùng các lệnh riêng trên khi chỉ cần kiểm tra không tái dựng dữ liệu.

## Phase 2: chỉ dùng clean_v1.1 cho công việc mới

```bash
make phase2-v11-validate
make phase2-v11-preflight
```

Validator kiểm tra benchmark frozen; preflight dùng Replay qua parser/Broker,
đủ tám tool và fault adapter, không chạy LLM. Không chạy lại generator/seal trên
dataset đã khóa. v1 cũ bị quarantine; `make phase2-validate` và các target
`phase2-kaggle-*` là đường lịch sử, không dùng để tạo thí nghiệm mới.

## Kết quả model đã có: đánh giá lại, không tự động chạy lại

Trước hết, nếu đang làm Phase 3, dùng `make phase3-audit` để đọc audit tĩnh của
bản v1. Lệnh hiện trả exit 1 (qua Make có thể là exit 2) vì **chưa accepted**,
không phải lỗi cần rerun Kaggle. Nó không sửa dữ liệu hay chạy LLM. Xem
[tiến độ Phase 3](phase3_progress.md); không gọi builder v1 để ghi đè draft.

Để kiểm tra workbench mới (bốn cặp riêng, không phải dataset v1), chọn output
và report chưa tồn tại:

```bash
.venv/bin/python scripts/verify_adversarial_workbench.py \
  --output results/phase3/workbench_local_check \
  --report results/phase3/workbench_local_check_receipt.json
```

Lệnh chạy 16 Replay, không gọi LLM, không cần credentials; chỉ sao chép môi
trường vào thư mục kết quả. Không ghi đè kết quả cũ và không tự tạo Test split.

Đợt mở rộng hiện hành có 12 cặp ứng viên riêng, chạy 48 Replay với data-scope
QA offline; cũng phải chọn hai đường dẫn chưa tồn tại:

```bash
.venv/bin/python scripts/verify_canonical_candidates.py \
  --output results/phase3/candidates_local_check \
  --report results/phase3/candidates_local_check_receipt.json
```

Không gọi script này như evaluator LLM/held-out Test. Receipt xác nhận fixture
QA với exact source/input hashes, không cấp semantic/Phase 3 acceptance.

Lớp review QA mới giữ nguyên 12 cặp, thêm typed utility + source evidence và
audit đủ 66 tổ hợp/nhóm. Dùng output/report mới chưa tồn tại:

```bash
.venv/bin/python scripts/verify_candidate_review.py \
  --output results/phase3/candidate_review_local_check \
  --report results/phase3/candidate_review_local_check_receipt.json
```

Đọc [contract review QA](../docs/benchmark/candidate_review_contract.md).
Không đưa private utility sidecars vào model context; không dùng script này
để chấm lại pilot cũ, tự cấp approval hoặc tự tạo split.

Pilot dữ liệu hiện hành là revision v2.2 của 12 cặp. Kiểm tra allowed-field
changes, neutral wording/length/group gates rồi chạy 48 typed Replay:

```bash
.venv/bin/python scripts/verify_canonical_revision.py \
  --output results/phase3/canonical_revision_local_check \
  --report results/phase3/canonical_revision_local_check_receipt.json
```

Output/report phải chưa tồn tại. v2.1 và các receipt trước chỉ dùng để đối chiếu,
không sửa tại chỗ. Đây chưa phải benchmark 70 family hoặc split cuối.

Batch hiện hành bổ sung tám cặp mới bên cạnh pilot v2.2. Chạy 32 Replay với
private mechanism rules và audit combined pool 20 ứng viên:

```bash
.venv/bin/python scripts/verify_mechanism_batch.py \
  --output results/phase3/mechanism_batch_local_check \
  --report results/phase3/mechanism_batch_local_check_receipt.json
```

Chọn đường dẫn chưa tồn tại. Không chép private rule sidecars vào model prompt;
không dùng script này như final evaluator hoặc cấp approval cho 70 family.

Lệnh tổng hợp v1 giữ lại để tái lập 28 cặp pilot v2.2, mechanism và linked-scope:

```bash
.venv/bin/python scripts/verify_phase3_pool.py \
  --output results/phase3/pool_local_check \
  --report results/phase3/pool_local_check_receipt.json
```

Chọn hai đường dẫn mới mỗi lần. 28 cặp tạo 112 Replay, không LLM/Kaggle run.
`qa_valid` khác `phase3_accepted`: hiện QA pass nhưng acceptance vẫn false.
Thêm `--require-acceptance` nếu cần CI chặn đóng phase; exit 2 sau khi lưu
report là kết quả đúng khi còn thiếu canonical/review/split/variants/freeze.
Không sửa hoặc retry dataset để làm xanh gate. Đọc
[contract linked-scope](../docs/benchmark/linked_scope_contract.md) cho giới hạn SQL.

Lệnh tổng hợp v2 giữ lại để tái lập bốn batch, gồm 12 transaction/sink-position:

```bash
.venv/bin/python scripts/verify_phase3_pool_v2.py \
  --output results/phase3/pool_v2_local_check \
  --report results/phase3/pool_v2_local_check_receipt.json
```

40 cặp tạo 160 Replay, 80 safe/80 negative. Chọn output/report chưa tồn tại.
`--require-acceptance` vẫn trả exit 2 khi thiếu gate toàn phase; không coi đó là
lỗi hạ tầng. Không cần chạy thêm từng script cũ để cộng lặp số lượt QA.
Đọc [contract transaction](../docs/benchmark/transaction_batch_contract.md).
Private rules và knowledge không được đưa vào model prompt hoặc worker bundle.

Lệnh tổng hợp v3 **lịch sử** chạy năm batch với mechanism rules v1:

```bash
.venv/bin/python scripts/verify_phase3_pool_v3.py \
  --output results/phase3/pool_v3_local_check \
  --report results/phase3/pool_v3_local_check_receipt.json
```

48 cặp tạo 192 Replay (96/96); output/report phải mới. Cờ `--require-acceptance`
trả exit 2 khi thiếu gate toàn phase dù fixture QA pass. Không chạy lại từng
verifier cũ để cộng lặp counts. Đọc [contract flow](../docs/benchmark/flow_batch_contract.md).

Lệnh QA snapshot admission trước dùng mechanism rules v2 và register nhận/gộp:

```bash
.venv/bin/python scripts/verify_canonical_admission.py \
  --output results/phase3/admission_local_check \
  --report results/phase3/admission_local_check_receipt.json \
  --require-acceptance
```

Output/report phải mới. Lệnh đối chiếu hash receipt/source/input cũ rồi tái dùng
160 standard paths; chạy mới 32 standard và sáu counterexample/control, tổng
38 fresh Replay. 48 ca → 46 đại diện tạm giữ/2 gộp; không phải family accepted.
Exit 2 có chủ đích khi `valid=true`, `phase3_accepted=false`; không retry để đổi
thành acceptance. [Contract](../docs/benchmark/mechanism_admission_contract.md)
và [tóm tắt](../docs/benchmark/mechanism_admission_summary.md) ghi giới hạn.
Không sửa source/input đã hash để làm gate xanh; tạo version cho thay đổi mới.

Lệnh QA snapshot disclosure trước:

```bash
.venv/bin/python scripts/verify_disclosure_batch.py \
  --output results/phase3/disclosure_local_check \
  --report results/phase3/disclosure_local_check_receipt.json \
  --require-acceptance
```

Chọn đường dẫn chưa tồn tại. 16 fresh Replay cho bốn cặp; tái dùng 192 standard
paths đã bind hash, không chạy lại toàn pool. Tổng 52 working/50 retained,
208 standard paths, 17 nhóm bảo thủ. Exit 2 từ acceptance gate là đúng dự kiến;
không phải lỗi runtime. [Contract](../docs/benchmark/disclosure_batch_contract.md)
ghi giới hạn exact-fragment/query và không cho phép suy diễn general provenance.

Lệnh QA snapshot completion-authoring trước:

```bash
.venv/bin/python scripts/verify_completion_batch.py \
  --output results/phase3/completion_local_check \
  --report results/phase3/completion_local_check_receipt.json \
  --require-acceptance
```

Chọn đường dẫn mới. 48 fresh Replay, tái dùng 208 standard paths; không phải
256 lượt mới. 64 stored/62 retained, 17 nhóm bảo thủ. `completion` trong tên
chỉ đợt authoring hướng tới hoàn thiện, không phải Phase 3 đã complete. Exit 2
acceptance gate đúng dự kiến. [Contract](../docs/benchmark/completion_batch_contract.md)
giữ nguyên scorer/runtime; không sửa source đã hash để làm gate xanh.

Lệnh **QA snapshot boundary lịch sử** bổ sung tám boundary pairs:

```bash
.venv/bin/python scripts/verify_boundary_batch.py \
  --output results/phase3/boundary_local_check \
  --report results/phase3/boundary_local_check_receipt.json \
  --require-acceptance
```

Chọn đường dẫn mới. 34 fresh Replay gồm 32 standard và hai safe alternatives;
tái dùng 256 standard, tổng standard 288. 72 stored/70 retained/20 nhóm bảo thủ.
Exit 2 với `valid=true`, `phase3_accepted=false` đúng dự kiến: chưa full-pool
admission/split/variants/seal. [Contract](../docs/benchmark/boundary_batch_contract.md)
ghi bounded coverage. Dùng `load_boundary_candidates` cho batch mới vì private
outcome có `final_policy`; không sửa loader/schema cũ đã hash. Final-policy và
derived-final fields phải được mang sang QA/release, không bỏ qua để chấm safe.

Lệnh **selection hiện hành** kiểm tra lại admission và grouped 40/30 manifest:

```bash
.venv/bin/python scripts/select_adversarial_canonicals.py \
  --report experiments/manifests/phase3_canonical_selection_v1_validation01.json \
  --check-existing --require-acceptance
```

Không ghi đè manifest. `valid`, `canonical_authoring_admitted` và
`canonical_split_valid` true; exit 2 vì Phase 3 còn variants/release/seal.
70 selected/20 nhóm, 40 Dev/30 Test, không có Replay/model run mới. Để audit vào
report riêng, bỏ `--check-existing` và chọn đường dẫn mới dưới `results/`.
Xem [contract](../docs/benchmark/canonical_selection_contract.md) và
[giới hạn strata](../docs/benchmark/canonical_selection_summary.md). Không đổi
seed, grouping hay assignment để phản ứng với kết quả Test. Không sửa source
đã hash; thêm module/phiên bản cho variant release tiếp theo.

[Báo cáo measured Dev](../docs/evaluation/measured_dev_pilot_report.md) chứa
lệnh tái tạo chính xác từ raw artifacts đã audit. Các script dùng output mới
và từ chối ghi đè; không thêm cờ overwrite. Source inference và source reporting
khác nhau, đều được ghi trong
[completion manifest](../experiments/manifests/measured_pilot_completion.json).

Khi cần đánh giá lại local, dùng `scripts/evaluate_clean_v11_dev.py`, sau đó
`scripts/audit_clean_v11_artifacts.py` với expected identity của đúng condition.
Không dùng evaluator v1 cũ cho v1.1. Không retry lỗi ngữ nghĩa để lấy điểm cao.

## Kaggle: chỉ khi có scope inference đã cho phép

1. Đọc [preflight của dự án](../.agents/skills/experiment-repro/references/kaggle-preflight.md)
   và skill Kaggle CLI trước thao tác remote.
2. Đóng gói từ source đã commit/push, worktree sạch, slug Dataset/kernel khác
   nhau. Với v1.1, dùng `scripts/prepare_kaggle_v11.py --help` để chọn profile,
   wheelhouse và protocol; không dùng lại bundle lịch sử tùy tiện.
3. Xác minh model file access, quota, CPU loader và exact mount preflight.
   Không chỉ kiểm tra metadata hoặc `cuda.is_available()`.
4. Dataset/kernel private, model revision cố định, không Test/private GT.
   Không thay tài khoản để gộp quota và không chấp nhận điều khoản thay owner.
5. Tải đúng kernel version vào thư mục mới, chọn raw artifacts cần thiết,
   kiểm tra hashes/checkpoints trước khi report. Không ghi đè artifact đã audit.

[Bài học Kaggle](kaggle_lessons.md) ghi lỗi mount, PYTHONPATH, title collision,
offline wheels và phân trang. `.venv/bin/kaggle` không có trong môi trường đã
kiểm tra; CLI dùng `python3 -m kaggle`. Không ghi secret/key vào Git.

## Ranh giới không được vượt

- Không chạy held-out Test, không đổi benchmark/evaluator/policy theo Test.
- Không đưa `knowledge/` vào runtime model hoặc inference bundle.
- Phase 3 chưa accepted; không tự tiến sang implementation defense Phase 4–5.
- Meta Llama còn pending; không chặn công việc Phase 3 vì model chưa có quyền.
