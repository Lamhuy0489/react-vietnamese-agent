# Vietnamese ReAct Tool-Agent Evaluation

Đồ án đánh giá khả năng, độ bền vững và an toàn của một tác nhân ReAct sử dụng
công cụ trong môi trường tiếng Việt giả lập (hành chính–học vụ đại học).

## Trạng thái

- Phase 1 và Phase 2 clean_v1.1 đã accepted (Phase 2 dưới automated-QA waiver);
  **Phase 3 adversarial_v2 đã nghiệm thu và khóa Test**: 350 attack + 350 benign,
  năm dạng biến thể. Xem [nghiệm thu và giới hạn](docs/benchmark/adversarial_release_v2_summary.md).
  Phase 4 chưa bắt đầu.
- Pilot đo hiệu suất Gemma 4 / Qwen 7B đã hoàn tất: strict 6/21 và 3/21 Dev,
  trung bình 11,66 và 10,92 giây/task; chưa phải kết quả Test hay kết luận chọn
  model. Xem [báo cáo](docs/evaluation/measured_dev_pilot_report.md).
- Kế hoạch gốc: file Word ở root và thư mục `plan/`.
- Contract triển khai đã chuẩn hóa: `docs/`.
- A0, smoke environment và clean benchmark 250 task đã được tạo; real-model
  smoke Phase 1 và Dev pilot Phase 2 chạy trên Kaggle. Đây chưa phải thí nghiệm
  chính của luận văn.

## Nguyên tắc cốt lõi

- Không dùng dữ liệu cá nhân thật.
- Email và webhook chỉ là mock, không có side effect mạng.
- Không lưu hidden chain-of-thought; chỉ lưu hành động và kết quả quan sát được.
- Held-out Test được niêm phong và không dùng để điều chỉnh hệ thống.
- GitHub là source of truth; Kaggle chỉ là inference worker.

## Cài đặt local

Yêu cầu Python 3.11 trở lên.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Kiểm tra setup:

```bash
python scripts/verify_setup.py
pytest
```

Chạy A0 smoke suite trên CPU bằng replay backend:

```bash
python scripts/build_smoke_environment.py
python scripts/validate_smoke_data.py
python scripts/run_smoke.py --backend replay
```

Replay suite phải hoàn thành 20/20 tác vụ, không crash và bao phủ đủ tám mock
tools. Kết quả sinh dưới `results/phase1/` và không được commit mặc định.

Sau khi cài dev dependencies:

```bash
ruff check .
mypy src scripts
```

## Kaggle Phase 1

Run được chấp nhận dùng Qwen2.5-3B-Instruct v1, Dataset v5 và kernel v4 trên
NVIDIA T4 với internet tắt. Trước mọi lần upload phải chạy:

```bash
make kaggle-bundle
make kaggle-bundle-validate
```

Xem trạng thái dễ đọc tại [knowledge/current_status.md](knowledge/current_status.md)
và manifest bằng chứng tại
[experiments/manifests/phase1_kaggle_v4.json](experiments/manifests/phase1_kaggle_v4.json).

## Clean benchmark Phase 2

v1.1 qua QA thực thi và khóa split không tách nhóm; Kaggle COMPLETE ngay lần
đầu: 21 terminal, 0 crash, 5/21 Dev diagnostic. Xem
[tiến độ v1.1 và giới hạn còn lại](knowledge/clean_v11_progress.md).
Các lệnh `phase2-*` cũ bên dưới vẫn chỉ audit bản v1 lỗi.

Cho bản mới, dùng `make phase2-v11-validate` và `make phase2-v11-preflight`.

**Bản v1 chưa đạt acceptance:** 30 cặp cùng fact/nguồn có group ID khác nhau,
trong đó 12 cặp nằm ở cả Dev và Test. Giữ bản khóa để lưu bằng chứng, chưa tạo
tag hay bắt đầu Phase 3. Xem [báo cáo audit](knowledge/integrity_audit_20260905.md).

Clean v1 có 250 task tổng hợp, chia group-wise thành 150 Dev và 100 Test bằng
seed 2026. Test đã niêm phong trước Dev pilot; Kaggle bundle chỉ chứa public Dev,
không chứa Test hoặc private ground truth.

```bash
make phase2-validate
```

Lệnh trên hiện **phải FAIL** vì v1 không hợp lệ. Test phần mềm pass nghĩa là
validator bắt đúng lỗi, không phải benchmark đạt acceptance. Đóng gói Kaggle
bị chặn cho đến khi có bản dữ liệu hợp lệ được phê duyệt.

Thiết kế và hạn chế dữ liệu được mô tả tại
[docs/clean_benchmark_design.md](docs/clean_benchmark_design.md) và
[docs/clean_data_card.md](docs/clean_data_card.md).

## Tài liệu

- [Research contract](docs/project/research_contract.md)
- [Phase map](docs/project/phase_map.md)
- [Project invariants](docs/project/invariants.md)
- [Architecture](ARCHITECTURE.md)
- [Team workflow](docs/project/team_workflow.md)
- [Project knowledge index](knowledge/README.md)

Không commit credential. Các file Kaggle hiện có trong `credential kaggle/` được
giữ ở local và bị `.gitignore` loại trừ toàn bộ.
