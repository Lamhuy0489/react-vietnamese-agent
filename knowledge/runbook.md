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
