# Vietnamese ReAct Tool-Agent Evaluation

Đồ án đánh giá khả năng, độ bền vững và an toàn của một tác nhân ReAct sử dụng
công cụ trong môi trường tiếng Việt giả lập (hành chính–học vụ đại học).

## Trạng thái

- Trạng thái hiện tại: **Phase 1 hoàn thành; Phase 2 đang ở cổng Dev pilot cuối**.
- Kế hoạch gốc: file Word ở root và thư mục `plan/`.
- Contract triển khai đã chuẩn hóa: `docs/`.
- A0, smoke environment và clean benchmark 250 task đã hoàn thành; real-model
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

Clean v1 có 250 task tổng hợp, chia group-wise thành 150 Dev và 100 Test bằng
seed 2026. Test đã niêm phong trước Dev pilot; Kaggle bundle chỉ chứa public Dev,
không chứa Test hoặc private ground truth.

```bash
make phase2-validate
make phase2-kaggle-bundle
make phase2-kaggle-bundle-validate
```

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
