# Runbook hiện hành

Chạy tại root repo. Dùng `.venv/bin/python`; không coi lệnh từ ghi chú v1
lịch sử là lệnh hiện hành. Đọc [bàn giao](handoff.md) trước khi chạy inference.

## Kiểm tra phần mềm và bộ nhớ

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

Lệnh **QA snapshot hiện hành** bổ sung tám boundary pairs:

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
