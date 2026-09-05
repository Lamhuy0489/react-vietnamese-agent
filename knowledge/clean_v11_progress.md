# Thay thế benchmark v1.1

Cập nhật 2026-09-06. Phase 2 còn đang thực hiện, chưa phải thí nghiệm cuối luận văn.

## Dữ liệu

- v1 giữ nguyên, chỉ lưu lịch sử; code tạo v1.1 dùng môi trường/template,
  không đọc split cũ hay dùng điểm model để chọn task.
- `data/clean/v1_1`: 250 task, quota 150 Dev/100 Test; nhóm cùng fact/evidence
  không tách xuyên category. 40 DB+document task tính học phí từ tín chỉ trong
  DB và đơn giá tài liệu; 4 task multi-source tính tổng dự toán hai nguồn.
- QA thực thi 250 oracle và mọi đường tool thay thế đã khai báo, kiểm tra
  retrieval target, SQL result equivalence, calculator và mock sink payload.
  Các cờ review gán sẵn của generator cũ bị loại bỏ, không dùng làm bằng chứng.
- Typed negative controls kiểm tra 24 không khớp 2024/-24/24.5, ngày sai,
  SQL trả sai kết quả, calculator khác kết quả và thiếu retrieval target.
- 50 canonical robustness được chọn bằng seed trước seal; chưa tạo variant
  hay chạy model trên Test. Schema/môi trường giữ identity cũ vì không đổi.
- Hash: `692ca92a214b0da87245ca7d11a074a74d416558f377bc448c125bd7d387be38`.

## Thực nghiệm

- CPU: public-only Dummy 21/21 terminal, 0 crash. Stub không chứng minh model
  trả lời đúng; đánh giá bằng private Dev GT ở local sau khi worker kết thúc.
- Checkpoint lưu trace/result mỗi task, checksum và input identity; resume
  bỏ qua mọi task terminal, kể cả semantic failure. Task dở có trace nhưng
  chưa receipt cần giữ lại và ghi deviation trước retry; không tự ghi đè.
- Chuẩn bị Kaggle: kiểm tra đúng archive đã commit trong cả mount archive và
  expanded/generated-directory, 8 tool và fault adapter, Dummy 21 task, resume.
- Pilot dự kiến: một Qwen2.5-3B-Instruct revision cố định, T4, private, offline,
  21 Dev task định trước; không đổi account để lấy thêm quota.

## Giới hạn phải báo cáo

QA tự động chỉ chứng minh schema, cấu trúc và hành vi đã kiểm tra; không thay
thế thẩm định độc lập về chất lượng ngôn ngữ/distractor. Owner đã bỏ review.
Evaluator chấp nhận các tool sequence được annotate, không mọi cách giải tương
đương về mặt ngôn ngữ; set-equal final answer hiện cần JSON list. Không gọi
điểm pilot là Test TSR hay kết quả chính luận văn.

## Chạy lại an toàn

```bash
python -m pytest
python scripts/preflight_clean_worker.py
python scripts/run_clean_v11_dev.py --backend dummy --output results/<fresh-run>
python scripts/evaluate_clean_v11_dev.py results/<fresh-run> --output results/<new-evaluation>.json
python scripts/prepare_kaggle_v11.py --owner huylmhuhu --output build/kaggle/<fresh-bundle>
```

Không chạy generator/seal lại trên version đã khóa. Tiến trình dài hạn ghi
trong `docs/project/phase_status.md`; kết quả Kaggle sẽ bổ sung sau khi audit.
