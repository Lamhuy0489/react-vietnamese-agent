# Bàn giao phiên làm việc

Cập nhật: 2026-09-07. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

**Phase 3 adversarial_v2 đã nghiệm thu và khóa Test**, source `c228a68`.
Phase 1 và Phase 2 clean_v1.1 cũng accepted. Tài liệu/knowledge đã cập nhật;
kiểm tra trạng thái remote theo bước 1. Phase 4 chưa bắt đầu. Không tiếp tục
authoring hoặc thêm canonical.
[Receipt đóng phase](../experiments/manifests/phase3_release_v2_closure.json),
[tóm tắt/giới hạn](../docs/benchmark/adversarial_release_v2_summary.md),
[seal](../data/adversarial/release_v2/seal.json).

70 canonical pairs, năm dạng mỗi branch, 350 attack + 350 benign. Mỗi branch
200 Dev/150 Test; 40/30 canonical families, 20 nhóm bảo thủ giữ trọn. Draft v1
và các snapshot pending cũ giữ nguyên; seal/review mới sở hữu acceptance.

## Bước tiếp theo

1. Kiểm tra `git status` và commit/remote để xác nhận đồng bộ, không giả định
   push đã xong từ nội dung file này. Đọc [phase status](../docs/project/phase_status.md).
2. Chạy hash-only:
   `.venv/bin/python scripts/assemble_adversarial_release.py --action check`,
   cùng setup/Ruff/mypy/pytest/knowledge-check theo [runbook](runbook.md).
3. **Chờ owner cho phép bắt đầu Phase 4.** Khi được phép, đọc phase4 và các
   contract liên quan; triển khai normalization/provenance trên Dev. Không nạp
   sealed Test, không chạy lại scripts authoring hoặc sửa source/data đã hash.
4. Public loader `load_split` mặc định Dev, không mở Test/private oracle.
   Chỉ `fixture.task` vào Runtime; overlay/resources thuộc tool environment.
   Bản Dev có 400 records; trace task ID giữ canonical, invocation/variant ID
   trong mapping dùng để nối đúng từng thí nghiệm.
5. Không cần tài khoản mới. Meta access còn thiếu chỉ ảnh hưởng Llama pilot,
   không chặn Phase 3/4. Không chạy Kaggle hay model experiment ngoài phạm vi.

## Bằng chứng

- Source mechanical `257cb1c`: 420 variants, 1.128 fresh reference paths.
  [Receipt](../experiments/manifests/phase3_mechanical_v1_validation01.json).
- Source linguistic `cad5b61`: 280 variants, 564 fresh reference paths.
  [Receipt](../experiments/manifests/phase3_linguistic_v1_validation01.json).
  Cả hai selected runs khớp stable summary của preflight; không model tuning.
- Source integration `c228a68`: tái chấm/archive **1.692 paths cũ**, gồm
  280 canonical standard + 1.400 variant standard + 12 alternatives.
  Không tính thành inference mới. 732 Test-assigned paths trước seal.
- Full trước seal: **782 tests pass**, hai post-seal-only tests skip. Sau seal:
  **132 tests pass**; 650 historical construction tests không collect trước
  import để tránh dùng Test trong development. Không xóa các bài kiểm thử đó.
- Setup/Ruff/mypy **146 files**, clean_v1.1 seal và adversarial seal đều pass.
  Trước commit: quét bốn credential values trên 43 file (giải nén archive) có
  0 match; quét cuối 52 file cũng 0 match. Knowledge-check sau cập nhật pass.
  Data/source/receipts cũ từ trước mốc mechanical không bị sửa.
- Seal SHA-256:
  `431b81118026bef6c60e33306e51df71160504579e76ea08fb4648005fa1cb6b`.
  Receipt khóa seal hash; Git giữ byte identity. Không sửa seal tại chỗ.
- Không LLM/held-out model run mới; điểm Gemma 6/21, Qwen7B 3/21 Dev cũ không đổi.

## Giới hạn

Owner waiver cho assistant self-review, không independent human review.
70 scenario families không phải 70 cơ chế trừu tượng độc lập. Grouped allocation
giữ tool-output poisoning 12 Dev/3 Test; không resplit/đổi nhãn để che lệch.
Replay chứng minh bounded fixture solvability/scoring, không ASR hay chất lượng
model. Phase 3 hoàn thành không có nghĩa toàn bộ đồ án hoàn thành.

Bộ nhớ này không chứa credentials, private ground truth, payload Test hoặc CoT.
Lịch sử công việc ở [progress](phase3_progress.md), [current status](current_status.md)
và [decision log](../docs/project/decision_log.md); trạng thái cũ không override seal.
