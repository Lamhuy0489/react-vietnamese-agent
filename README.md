# Vietnamese ReAct Tool-Agent Evaluation

Đồ án đánh giá khả năng, độ bền vững và an toàn của một tác nhân ReAct sử dụng
công cụ trong môi trường tiếng Việt giả lập (hành chính–học vụ đại học).

## Trạng thái

- Giai đoạn hiện tại: **Phase 1 — A0 baseline**.
- Kế hoạch gốc: file Word ở root và thư mục `plan/`.
- Contract triển khai đã chuẩn hóa: `docs/`.
- Chưa triển khai A0 hay chạy thí nghiệm chính.

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

## Tài liệu

- [Research contract](docs/project/research_contract.md)
- [Phase map](docs/project/phase_map.md)
- [Project invariants](docs/project/invariants.md)
- [Architecture](ARCHITECTURE.md)
- [Team workflow](docs/project/team_workflow.md)

Không commit credential. Các file Kaggle hiện có trong `credential kaggle/` được
giữ ở local và bị `.gitignore` loại trừ toàn bộ.
